# Copyright 2022 by Cyril Joder.
# All rights reserved.
# This file is part of merlinator, and is released under the 
# "MIT License Agreement". Please see the LICENSE file
# that should have been included as part of this package.


import tkinter as tk
from tkinter.ttk import Treeview
from PIL import Image, ImageTk
import os.path, shutil, uuid
from time import time
import logging
from pydub import AudioSegment
from mutagen.mp3 import MP3

from io_utils import *



class MerlinTree(Treeview):

    def __init__(self, parent, root=None):
        Treeview.__init__(self, parent, selectmode='browse', show='tree')
        if root is None:
            self.rootGUI = parent
        else:
            self.rootGUI = root
        
        
        self.bind('<Button-1>', self.rootGUI.mouseclick)
        self.bind('<B1-Motion>', self.rootGUI.movemouse)
        self.bind("<ButtonRelease-1>", self.rootGUI.mouserelease)
        self.bind("<Control-Up>", self.moveUp)
        self.bind("<Control-Down>", self.moveDown)
        self.bind("<Control-Left>", self.moveParentDir)
        self.bind("<KeyPress-Control_L>", self.disable_arrows)
        self.bind("<KeyRelease-Control_L>", self.enable_arrows)
        self.bind("<KeyPress-Control_R>", self.disable_arrows)
        self.bind("<KeyRelease-Control_R>", self.enable_arrows)
        
        self.bind('<<TreeviewSelect>>', self.rootGUI.synchronise_selection)
        
        self.bind('<Double-Button-1>', self.play_sound)

    def disable_arrows(self, *args):
        temp = self.bind_class('Treeview', '<Up>')
        if temp: 
            self.boundUp = self.bind_class('Treeview', '<Up>')
        temp = self.bind_class('Treeview', '<Down>')
        if temp:
            self.boundDown = temp
        temp = self.bind_class('Treeview', '<Left>')
        if temp:
            self.boundLeft = temp
        self.unbind_class('Treeview', '<Up>')
        self.unbind_class('Treeview', '<Down>')
        self.unbind_class('Treeview', '<Left>')
        
    def enable_arrows(self, *args):
        self.bind_class('Treeview', '<Up>', self.boundUp)
        self.bind_class('Treeview', '<Down>', self.boundDown)
        self.bind_class('Treeview', '<Left>', self.boundLeft)
        
        
    def moveUp(self, *args):
        node = self.selection()
        if node:
            self.move(node, self.parent(node), self.index(node)-1)
            self.see(node)
            self.rootGUI.sync_buttons_main()
            self.rootGUI.sync_buttons_fav()
            
    def moveDown(self, *args):
        node = self.selection()
        if node:
            self.move(node, self.parent(node), self.index(node)+1)
            self.see(node)
            self.rootGUI.sync_buttons_main()
            self.rootGUI.sync_buttons_fav()
            
    def moveParentDir(self, *args):
        node = self.selection()
        if node and self.parent(node) != '':
            self.move(node, self.parent(self.parent(node)), 'end')
            self.see(node)
            self.rootGUI.sync_buttons_main()
            self.rootGUI.sync_buttons_fav()

    def get_ancestors(self, node):
        res = [node]
        parent = self.parent(node)
        while parent:
            res.append(parent)
            parent = self.parent(parent)
        return res
 
        

class MerlinMainTree(MerlinTree):


    COL = ("Favori", "imagepath", "soundpath", "id", "parent_id", "order", "nb_children", 
           "fav_order", "type", "limit_time", "add_time", 
           "uuid", "title")

    dir_of_merlinator = os.path.dirname(os.path.realpath(__file__))
    rootItem = {'id': 1, 'parent_id': 0, 'order': 0, 'nb_children': 0, 
                'fav_order': 0, 'type': 1, 'limit_time': 0, 'add_time': 0, 
                'uuid': '', 'title': 'Root', 'imagepath': '', 'soundpath': ''}
    favItem = {'id': 2, 'parent_id': 1, 'order': 0, 'nb_children': 0,
               'fav_order': 0, 'type': 10, 'limit_time': 0, 'add_time': 0, 
               'uuid': 'cd6949db-7c5f-486a-aa2b-48a80a7950d5', 'title': 'Merlin_favorite', 
               'imagepath': os.path.join(dir_of_merlinator,'../res/defaultPics.zip'), 'soundpath': ''}
    recentItem = {'id': 3, 'parent_id': 1, 'order': 1, 'nb_children': 0, 
                  'fav_order': 0, 'type': 18, 'limit_time': 0, 'add_time': 0, 
                  'uuid': '8794f486-c461-4ace-a44b-85c359f84017', 'title': 'Merlin_discover', 
                  'imagepath':os.path.join(dir_of_merlinator,'../res/defaultPics.zip'), 'soundpath': ''}
    defaultItems = [rootItem, favItem, recentItem]
    
    def __init__(self, parent, root=None):
        MerlinTree.__init__(self, parent, root)
        
        self.currently_selected = []
        self.iid_Merlin_favorite = None
        self.iid_Merlin_discover = None


        self["columns"] = MerlinMainTree.COL
        self.column("#0", width=300)
        self.column("Favori", width=20, minwidth=10, stretch=tk.NO)
        # self.column("id", width=20, minwidth=10, stretch=tk.NO)
        # self.column("parent_id", width=20, minwidth=10, stretch=tk.NO)
        # self.column("order", width=20, minwidth=10, stretch=tk.NO)
        # self.column("nb_children", width=20, minwidth=10, stretch=tk.NO)
        # self.column("fav_order", width=20, minwidth=10, stretch=tk.NO)
        # self.column("type", width=20, minwidth=10, stretch=tk.NO)
        # self.column("limit_time", width=20, minwidth=10)
        # self.column("add_time", width=20, minwidth=10)
        # self.column("uuid", width=100, minwidth=50)
        # self.column("title", width=100, minwidth=50)
        self["displaycolumns"]=["Favori"]
        
        # self.heading('#0',text='Nom', anchor=tk.W)
        # for key in MerlinMainTree.COL:
            # self.heading(key, text=key, anchor=tk.W)
        
        self.tag_configure("directory", foreground="grey")
        
    
    def populate(self, items, thumbnails, overwrite):
        if overwrite:
            # clear existing data
            for c in self.get_children():
                self.delete(c)
            if self.iid_Merlin_discover:
                self.delete(self.iid_Merlin_discover)
                self.iid_Merlin_discover = None
            if self.iid_Merlin_favorite:
                self.delete(self.iid_Merlin_favorite)
                self.iid_Merlin_favorite = None
        
        mapiid = dict()
        mapiid[1] = ''
        offsets = dict()
        offsets[''] = len(self.get_children())
        
        merge = False
        for item in (item for item in items if item['parent_id']==1):
            for c in self.get_children():
                if self.item(c, 'text')[3:] == item['title'] and \
                   self.set(c, 'uuid') == item['uuid']:
                    merge = True
                    break
            if merge:
                break
        if merge:
            self.focus_force()
            question = "Les playlists ont des éléments en commun. Fusionner les deux playlist?\n(cliquer sur Non pour joindre la nouvelle playlist à la fin)"
            answer = tk.messagebox.askyesno("Fusionner?",question)
            if not answer:
                merge = False
        
        # adding data
        for item in items:
            favorite = '♥' if item['fav_order'] else ''
            data = tuple([ favorite] + \
                [item[key] for key in MerlinMainTree.COL[1:]])
            iid = item['id']
            if item['parent_id']==1:
                parent = ''
            else:
                parent = item['parent_id']
            if item['type']==1: # root
                continue
            elif item['type'] in {10,42} and self.iid_Merlin_favorite: # favoris
                continue
            elif item['type'] in {18,50} and self.iid_Merlin_discover: # ajouts récents
                continue
            
            data = tuple([ favorite] + \
                [item[key] for key in MerlinMainTree.COL[1:]])
            parent = mapiid[item['parent_id']]
            
            if merge:
                for c in self.get_children(parent):
                    if self.item(c, 'text')[3:] == item['title'] and \
                       self.set(c, 'uuid') == item['uuid']:
                        mapiid[item['id']] = c
                        offsets[c] = len(self.get_children(c))
                        break
                if item['id'] in mapiid:
                    offsets[parent] -= 1
                    continue
            
            iid = self.insert(parent, item['order']+offsets[parent], text=item['title'], values=data, image=thumbnails[item['uuid']])
            mapiid[item['id']] = iid
            offsets[iid] = 0
            self.set(iid, 'id', iid)
            self.set(iid, 'parent_id', parent)
            
            
            if item['type']%32 in [2, 6]: # directory 
                self.item(iid, tags="directory")
                self.item(iid, text=' \u25AE ' + self.item(iid, 'text'))
            elif item['type']%32 == 10: # favoris
                self.item(iid, tags="directory")
                self.item(iid, text=' \u25AE ' + self.item(iid, 'text'))
                self.iid_Merlin_favorite = iid
                self.detach(iid)
            elif item['type']%32==18: # ajouts récents
                self.item(iid, tags="directory")
                self.item(iid, text=' \u25AE ' + self.item(iid, 'text'))
                self.iid_Merlin_discover = iid
                self.detach(iid)
            else:
                self.item(iid, text=' \u266A ' + self.item(iid, 'text'))
                if item['fav_order']>0:
                    self.item(iid, tags=("sound", "favorite"))
                else:
                    self.item(iid, tags="sound")
                
        self.update()
                
        
    def make_item_list(self):
        
        root_item = MerlinMainTree.rootItem
        children = self.get_children('')
        root_item['nb_children'] = len(children)
        items = [root_item]
        self.nb_fav = len(self.tag_has("favorite"))
        counter = 1
        for order, c in enumerate(children):
            sublist, counter = self.subtree_to_list(c, counter, order)
            items.extend(sublist)
        order = len(children)
        if self.iid_Merlin_favorite:
            item = format_item(self.set(self.iid_Merlin_favorite))
            counter += 1
            item['id'] = counter
            item['order'] = order
            order += 1
            item['parent_id'] = root_item['id']
            root_item['nb_children'] += 1
            item['nb_children'] = self.nb_fav
            items.append(item)
        if self.iid_Merlin_discover:
            item = format_item(self.set(self.iid_Merlin_discover))
            counter += 1
            item['id'] = counter
            item['order'] = order
            order += 1
            item['parent_id'] = root_item['id']
            root_item['nb_children'] += 1
            items.append(item)
        
        return items
        
        
    def subtree_to_list(self, node, counter=0, order=0, parent=1):
        item = format_item(self.set(node))
        children = self.get_children(node)
        counter += 1
        item['id'] = counter
        item['order'] = order
        item['parent_id'] = parent
        item['nb_children'] = len(children)
        item['title'] = self.item(node, "text")[3:]
        if self.tag_has('favorite', node):
            item['fav_order'] = self.nb_fav - self.rootGUI.fav_tree.index(node)
        items = [item]
        for order, c in enumerate(children):
            sublist, counter = self.subtree_to_list(c, counter, order, item['id'])
            items.extend(sublist)
        return items, counter
           
    def set_selection(self, *args):
        self.current_selection = self.selection()
      
    
    def reset_selection(self, *args):
        self.selection_set(self.current_selection)
        self.focus(self.current_selection)

    def deleteNode(self, event=None, forceNode=None):
        if forceNode:
            node = forceNode
            if (children:=self.get_children(node)):
                for child in children:
                    self.deleteNode(event, child)
            fav_tree = self.rootGUI.fav_tree
            if fav_tree.exists(node):
                fav_tree.delete(node)
            self.delete(node)
        else:
            node = self.selection()
            if (event and event.widget in [self.rootGUI, self]) or \
                event is None:
                if not node:
                    return
                if self.tag_has('directory', node):
                    node_type = 'menu'  
                else:
                    node_type = 'fichier'
                detail = ''
                if node_type == 'menu' and self.get_children(node):
                    detail = " et tout ce qu'il contient"
                question = f"Effacer le {node_type} '{self.item(node, 'text')[3:]}'{detail} ?"
                answer = tk.messagebox.askyesno("Confirmation",question)
                if answer:
                    self.deleteNode(event, node)
                self.rootGUI.sync_buttons_main()
                self.rootGUI.sync_buttons_fav()


    def add_menu(self):
        current_node = self.selection()
        tt = self.set(current_node,'type')
        if tt== '2' or tt == '6' :
            #current selection is a directory, insert a child
            iid = self.insert(current_node, 0, text=' \u25AE Nouveau Menu', tags="directory")
        else:
            #current selection is a file, insert at the same level
            iid = self.insert(self.parent(current_node), self.index(current_node)+1, text=' \u25AE Nouveau Menu', tags="directory")
        self.set(iid, 'type', '6')
        self.set(iid, 'add_time', str(int(time())))
        self.set(iid, 'title', 'Nouveau Menu')
        self.set(iid, 'uuid', str(uuid.uuid4()))
        self.focus(iid)
        self.selection_set(iid)
        self.update()
        self.rootGUI.title_entry.focus_set()

    def find_common_prefix_and_suffix(self,basenames):
        if len(basenames) < 2:
            return None, None
        common_prefix = None
        common_suffix = None
        for basename in basenames:
            if common_prefix is None:
                common_prefix = basename
                common_suffix = basename[::-1]
            else:
                common_prefix = os.path.commonprefix([common_prefix, basename])
                common_suffix = os.path.commonprefix([common_suffix, basename[::-1]])
        return common_prefix, common_suffix[::-1]
    def shorten_filename(self,filename, trim_prefix, trim_suffix):
        if trim_prefix is None and trim_suffix is None:
            filename = os.path.splitext(os.path.basename(filename))[0]
        else:
            if trim_prefix is not None and filename.startswith(trim_prefix):
                filename = filename[len(trim_prefix):]
            if trim_suffix is not None and filename.endswith(trim_suffix):
                filename = filename[:-len(trim_suffix)]
        fb = filename.encode('UTF-8')
        if len(fb) > 60:
            fb = fb[:60]
        return fb.decode('UTF-8')


    def add_sound(self):
        current_node = self.selection()
        tt = self.set(current_node,'type')
        if tt== '2' or tt == '6' :
            #current selection is a directory, insert a child
            parent_node = current_node
            insert_index = 9999999
        else:
            #current selection is not a directory, insert at the same level
            parent_node = self.parent(current_node)
            insert_index = self.index(current_node)+1

        playlist_dirname = os.path.dirname(self.rootGUI.playlistpath)
        filepaths = filedialog.askopenfilename(filetypes=[('mp3', '*.mp3')], multiple=True)
        if not filepaths:
            return

        for filepath in filepaths:
            dirname = os.path.dirname(filepath)
            if dirname == playlist_dirname:
                messagebox.showerror('Error', 'Cannot add sound file from the same directory as the playlist')
                return
                
        common_prefix, common_suffix = self.find_common_prefix_and_suffix(filepaths)

        for filepath in filepaths:
            display_name = self.shorten_filename(filepath, common_prefix, common_suffix)

            new_uuid = str(uuid.uuid4())
            new_basename = new_uuid+".mp3"
            new_filepath = os.path.join(playlist_dirname,new_basename)

            must_convert = True
            try:
                audiofile = MP3(filepath)
                if audiofile.info.bitrate == 128000 and audiofile.info.channels == 2 and audiofile.info.sample_rate == 44100:
                    must_convert = False
            except:
                pass
            
            if must_convert:
                AudioSegment.from_file(filepath).export(new_filepath, format="mp3", bitrate="128k", parameters=["-ac", "2", "-ar", "44100"])    
                logging.warning("encoded %s to %s", filepath, new_filepath)
            else:
                shutil.copyfile(filepath, new_filepath)
                logging.warning("copied %s to %s", filepath, new_filepath)

            
            iid = self.insert(parent_node, insert_index, text=' \u266A ' + display_name, tags='sound')
            self.set(iid, 'type', '4')
            self.set(iid, 'soundpath', new_filepath)
            self.set(iid, 'add_time', str(int(time())))
            self.set(iid, 'uuid', new_uuid)
        if len(filepaths)==1:
            self.focus(iid)
            self.selection_set(iid)
        self.update()

    def select_image(self):
        current_node = self.selection()
        playlist_dirname = os.path.dirname(self.rootGUI.playlistpath)
        if not current_node:
            return
        uuid = self.set(current_node, 'uuid')
        if uuid:
            initfile = uuid+'.jpg'
        else:
            raise Exception("no uuid for node")
        dest_filepath = os.path.join(playlist_dirname, initfile)
        filepath = filedialog.askopenfilename(filetypes=[('images', '.jpg .png')])
        if not filepath:
            return
        with Image.open(filepath) as image:
            image_small = image.convert('RGB').resize((128, 128), Image.ANTIALIAS)
            image_small.save(dest_filepath, "JPEG", mode='RGB', optimize=False, progressive=False)
                
        with Image.open(dest_filepath) as image:
            icon_small = image_small.resize((40, 40), Image.ANTIALIAS)
            self.rootGUI.thumbnails[uuid] = ImageTk.PhotoImage(icon_small)
        
        self.item(current_node, image=self.rootGUI.thumbnails[uuid])
        self.set(current_node, 'imagepath', dest_filepath)
        self.update()
        
    
    
    def toggleFavorite(self, *args):
        node = self.selection()
        if self.tag_has('favorite', node):
            self.removeFromFavorite(node)
        else:
            self.addToFavorite(node)
        
    def addToFavorite(self, node, index='end'):
        if node and self.tag_has('sound', node) and not self.tag_has('favorite', node):
            self.item(node, tags=('sound', 'favorite'))
            self.set(node, 'Favori', '♥')
            self.rootGUI.fav_tree.insert('', index, iid=node, \
                                         text=self.item(node, 'text'), \
                                         image=self.item(node, 'image'))
            self.rootGUI.fav_tree.selection_set(node)
            self.rootGUI.fav_tree.see(node)
            self.update()
            self.rootGUI.fav_tree.update()
            self.rootGUI.sync_buttons_fav()
        
    def removeFromFavorite(self, node):
        node = self.selection()
        if node and self.tag_has('sound', node):
            self.item(node, tags=('sound'))
            self.set(node, 'Favori', '')
            self.rootGUI.fav_tree.delete(node)
            self.update()
            self.rootGUI.fav_tree.update()
            self.rootGUI.sync_buttons_fav()
            
            
    def play_sound(self, event):
        if self.rootGUI.enable_audio:
            node = self.identify_row(event.y)
            if self.tag_has('sound', node):
                self.rootGUI.audio_widget.Play()
 

    

class MerlinFavTree(MerlinTree):
    
    def __init__(self, parent, root=None):
        MerlinTree.__init__(self, parent, root)
        
    
    def populate(self, main_tree, overwrite):
        if overwrite:
            # clear existing data
            for c in self.get_children():
                self.delete(c)
        
        # add data
        nb_children = len(self.get_children())
        fav_list = sorted([(int(main_tree.set(node,'fav_order')), node) for node in main_tree.tag_has('favorite') if not self.exists(node)], reverse=True)
        for order, fav in enumerate(fav_list):
            node = fav[1]
            self.insert('', order+nb_children, iid=node, text=main_tree.item(node, 'text'), \
                        image=main_tree.item(node, 'image'))
        self.update()
    
    
    def play_sound(self, event):
        if self.rootGUI.enable_audio:
            node = self.identify_row(event.y)
            self.rootGUI.audio_widget.Play()
 