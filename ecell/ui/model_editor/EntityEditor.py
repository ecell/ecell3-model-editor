#::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
#
#       This file is part of the E-Cell System
#
#       Copyright (C) 1996-2007 Keio University
#       Copyright (C) 2005-2007 The Molecular Sciences Institute
#
#::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
#
#
# E-Cell System is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
# 
# E-Cell System is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public
# License along with E-Cell System -- see the file COPYING.
# If not, write to the Free Software Foundation, Inc.,
# 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
# 
#END_HEADER
#
#'Design: Gabor Bereczki <gabor@e-cell.org>',
#'Design and application Framework: Koichi Takahashi <shafi@e-cell.org>',
#'Programming: Gabor Bereczki' at
# E-CELL Project, Lab. for Bioinformatics, Keio University.
#
import os
import os.path

import gtk

import ecell.model.objects as objs
import ecell.util
from ecell.DMInfo import *

from ecell.ui.model_editor.ModelEditor import *
from ecell.ui.model_editor.PropertyList import *
from ecell.ui.model_editor.ViewComponent import *
from ecell.ui.model_editor.Constants import *
from ecell.ui.model_editor.ShapePropertyComponent import *
from ecell.ui.model_editor.ResizeableText import *

import ecell.ui.model_editor.Utils as utils

class EntityEditor(ViewComponent):
    def __init__( self, aParentWindow, pointOfAttach, anEntityType, aThirdFrame=None):
        # call superclass
        ViewComponent.__init__( self,  pointOfAttach, 'attachment_box' , 'ObjectEditor.glade' )
        
        self.theParentWindow = aParentWindow
        self.theModelEditor = self.theParentWindow.theModelEditor
        self.theModel = self.theModelEditor.theModel
        self.theType = anEntityType
        self.theDisplayedEntity = None

        self.updateInProgress = False
        self.theInfoBuffer = gtk.TextBuffer()
        self.theDescriptionBuffer = gtk.TextBuffer()
        self['classname_desc'].set_buffer( self.theDescriptionBuffer )
        self['user_info'].set_buffer( self.theInfoBuffer )

        # add handlers
        self.addHandlers({
                'on_combo-entry_changed' : self.__change_class,
                'on_editor_notebook_switch_page' : self.__select_page,
                'on_ID_entry_editing_done' : self.__change_name,
                'on_user_info_move_focus' : self.__change_info
                })


        # initate Editors
        self.thePropertyList = PropertyList(self.theParentWindow, self['PropertyListFrame'] )
        aNoteBook=ViewComponent.getWidget(self,'editor_notebook')

        if aThirdFrame != None:
            #Add the ShapePropertyComponent
            aShapeFrame=gtk.VBox()
            aShapeFrame.show()
            aShapeLabel=gtk.Label('ShapeProperty')
            aShapeLabel.show()
            aNoteBook.append_page(aShapeFrame,aShapeLabel)
            self.theShapeProperty = ShapePropertyComponent(self.theParentWindow, aShapeFrame )
            self.thePropertyList.hideButtons()
        else:
            aNoteBook.set_tab_pos( gtk.POS_TOP )
            desc_vertical = self['desc_vertical']
            desc_horizontal = self['desc_horizontal']
            infoDesc = self['info_desc']
            proplist = self['PropertyListFrame']
            vertical = self['vertical_holder']
            horizontal = self['horizontal_holder']
            horizontal.remove( proplist)
            desc_horizontal.remove( infoDesc )
            vertical.pack_end( proplist)
            vertical.child_set_property( proplist, "expand", True )
            vertical.child_set_property( proplist, "fill", True )
            vertical.child_set_property( horizontal, "expand", False )
            desc_vertical.pack_end( infoDesc )
            vertical.show_all()
            desc_vertical.show_all()
            
        
        # make sensitive change class button for process
        if self.theType == PROCESS:
            self['class_combo'].set_sensitive( True )
                
        self.setDisplayedEntity( None )

    def getShapeProperty( self ):
        return self.theShapeProperty
                     
    def close( self ):
        """
        closes subcomponenets
        """
        self.thePropertyList.close()
        ViewComponent.close(self)

    def getDisplayedEntity( self ):
        """
        returns displayed entity
        """
        return self.theDisplayedEntity

    def bringToTop( self ):
        self['ID_entry'].grab_focus()

    def update ( self ):
        """
        """
        # update Name
        if self.theModelEditor.getMode() == ME_DESIGN_MODE:
            self.updateEditor()
        if self.theDisplayedEntity != self.thePropertyList.getDisplayedEntity():
            self.thePropertyList.setDisplayedEntity( self.theDisplayedEntity )
        else:
            # update propertyeditor
            self.thePropertyList.update()

    def updateEditor( self ):
        self.updateInProgress = True
        if self.theDisplayedEntity !=None:
            nameText = self.theDisplayedEntity.localID
        else:
            nameText = ''
        self['ID_entry'].set_text( nameText )

        sensitiveFlag = False
        if self.theDisplayedEntity != None:
            sensitiveFlag = True
        self['user_info'].set_sensitive( sensitiveFlag )
        if sensitiveFlag and self.theDisplayedEntity.parent == None:
            sensitiveFlag = False
        self['ID_entry'].set_sensitive( sensitiveFlag )
        

        # delete class list from combo
        self['class_combo'].entry.set_text('')
        self['class_combo'].set_popdown_strings([''])
        self['class_combo'].set_sensitive( False )
        self['class_combo'].set_data( 'selection', '' )
        descText = ''

        if self.theDisplayedEntity != None:
            # get actual class
            actualClass = self.theDisplayedEntity.klass

            if isinstance( actualClass, objs.Process ):
                self['class_combo'].set_sensitive( True )
            # get class list
            classList = self.theModelEditor.getDMInfo().getClassInfoList( type = DM_TYPE_PROCESS )

            self['class_combo'].set_popdown_strings(
                map( lambda i: i.name, classList ) )
            # select class
            self['class_combo'].entry.set_text( actualClass.name )
            self['class_combo'].set_data( 'selection', actualClass )
            self.__setDescriptionText( actualClass.description )

        # update syspath if apropriate
        syspathText = ''
        if self.theDisplayedEntity !=None:
            syspathText = self.theModelEditor.getModel().getFullIDOf( self.theDisplayedEntity ).getSuperSystemPath()
        self['path_entry'].set_text( str( syspathText ) )

        infoText = ''
        if self.theDisplayedEntity != None :
            try:
                infoText = self.theDisplayedEntity.getAnnotation('info')
            except:
                pass
        self.__setInfoText( infoText )
        self.updateInProgress = False

    def setDisplayedEntity( self, selectedEntity ):
        assert selectedEntity == None or isinstance( selectedEntity, objs.Entity )
        self.theDisplayedEntity = selectedEntity
        self.thePropertyList.setDisplayedEntity( self.theDisplayedEntity )
        self.updateEditor()

    def addLayoutEditor( self, aLayoutEditor ):
        pass

    def changeClass( self, newClass ):
        currentClass = self.theModelEditor.getModel().getEntityClassName( self.theDisplayedEntity )
        if currentClass == newClass:
            return
        aCommand = ChangeEntityClass( self.theModelEditor, newClass, self.theDisplayedEntity )
        self.theModelEditor.doCommandList( [ aCommand ] )

    def changeName( self, newName ):
        if not ecell.util.validateIDString( newName ):
            utils.showPopupMessage(
                utils.OK_MODE,
                "Only alphanumeric characters and _ are allowed in "
                + "entity names!", ME_ERROR )
            return
        oldID = self.theModelEditor.getModel().getFullIDOf(
            self.theDisplayedEntity )
        obj = self.theLayout.getObjectByFullID( oldID )
        newID = identifiers.FullID( oldID )
        newID.id = newName
        aCommand = SetObjectProperty(
            self.theLayout, obj.getID(), OB_PROP_FULLID, newID )
        if not aCommand.isExecutable():
            utils.showPopupMessage( utils.OK_MODE, "OOPS", ME_ERROR )
            return
        self.theModelEditor.doCommandList ( [ aCommand ] )
        self.theParentWindow.selectEntity( [ newID ] )
        self.updateEditor()

    def changeInfo( self, newInfo ):
        aCommand = SetEntityInfo( self.theModelEditor, self.theDisplayedEntity, newInfo )
        self.theModelEditor.doCommandList( [ aCommand ] )

    # -- Private methods/Signal Handlers 
    def __change_class( self, *args ):
        """
        called when class is to be changed
        """
        if args[0].get_text() == '':
            return
        if self.updateInProgress:
            return
        newClass = self['class_combo'].entry.get_text()
        self.changeClass( newClass )

    def __select_page( self, *args ):
        """
        called when editor pages are selected
        """
        pass

    def __change_name ( self, *args ):
        if self.updateInProgress:
            return
        newName = self['ID_entry'].get_text()
        self.changeName( newName )
        
    def __change_info( self, *args ):
        if self.updateInProgress:
            return
        newInfo = self.__getInfoText()
        self.changeInfo( newInfo )

    def __setDescriptionText( self, textString ):
        self.theDescriptionBuffer.set_text( textString )

    def __getInfoText( self ):
        endIter = self.theInfoBuffer.get_end_iter()
        startIter = self.theInfoBuffer.get_start_iter()
        return self.theInfoBuffer.get_text( startIter, endIter, True )

    def __setInfoText( self, textString ):
        self.theInfoBuffer.set_text( textString )

