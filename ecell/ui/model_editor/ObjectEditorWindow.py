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
#'Programming: Sylvia Tarigan' at
# E-CELL Project, Lab. for Bioinformatics, Keio University.
#
import os
import os.path

import gtk
import gobject

from ecell.ui.model_editor.ModelEditor import *
from ecell.ui.model_editor.ViewComponent import *
from ecell.ui.model_editor.Constants import *
from ecell.ui.model_editor.EntityEditor import EntityEditor
from ecell.ui.model_editor.VariableReferenceEditorComponent import *
from ecell.ui.model_editor.LayoutManager import LayoutManager
from ecell.ui.model_editor.Layout import Layout
from ecell.ui.model_editor.viewobjects import EditorObject
from ecell.ui.model_editor.LayoutCommand import *
from ecell.ui.model_editor.ResizeableText import *

class ObjectEditorWindow :
    def __init__( self, aModelEditor, aLayoutName, anObjectId ):
        """
        sets up a modal dialogwindow displaying 
        the EntityEditor and the ShapeProperty
        # objectID can be None, String, list of strings
        """ 
        self.theModelEditor = aModelEditor  
        self.theTopFrame = gtk.VBox()
        self.theEntityEditor = EntityEditor( self, self.theTopFrame,'Entity', True )
        self.theLastDisplayedEntity = None
        self.theShapeProperty = self.theEntityEditor.getShapeProperty()
        self.setDisplayObjectEditorWindow(aLayoutName, anObjectId)

    def setDisplayObjectEditorWindow(self,aLayoutName, anObjectID):
        self.theLayoutName = aLayoutName
        self.theLayout =self.theModelEditor.theLayoutManager.getLayout(aLayoutName)
        self.theObjectDict = {}
        self.theType = "None"
        if anObjectID == None:
            objectIDList = []
        elif type(anObjectID ) == str:
            objectIDList = [ anObjectID ]
        elif type( anObjectID ) in ( list, tuple ):
            objectIDList = anObjectID
            
        for anID in objectIDList:
            anObject = self.theLayout.getObject( anID ) 
            self.theObjectDict[anID] = anObject 
            aType = anObject.getProperty( OB_PROP_TYPE )
            if self.theType == "None":
                self.theType = aType
            elif self.theType != aType:
                self.theType = "Mixed"
        self.selectEntity( objectIDList )
        self.theShapeProperty.setDisplayedShapeProperty( self.theObjectDict, self.theType )

    def bringToTop( self ):
        self.theModelEditor.theMainWindow.setSmallWindow( self.theTopFrame )
        self.theEntityEditor.bringToTop()

    def update(self, aType = None, aFullID = None):
        #if aFullID not None, see whether all objects exist
        deletion = False

        existObjectList = self.theLayout.getObjectList()
        for anObjectID in self.theObjectDict.keys():
            if anObjectID not in existObjectList:
                self.theObjectDict.__delitem__( anObjectID )
                deletion = True
        if deletion:
            self.setDisplayObjectEditorWindow(
                self.theLayoutName,
                self.theObjectDict.keys() )
        else:
            self.updatePropertyList()
            self.updateShapeProperty()

    def updatePropertyList ( self, aFullID = None ):
        """
        in: anID where changes happened
        """
        # get selected objectID
        propertyListEntity = self.theEntityEditor.getDisplayedEntity()
        # check if displayed fullid is affected by changes

        if propertyListEntity != self.theLastDisplayedEntity:
            self.theEntityEditor.setDisplayedEntity ( self.theLastDisplayedEntity )
        else:
            self.theEntityEditor.update()

    def updateShapeProperty(self):
        if self.theModelEditor.getMode() != ME_DESIGN_MODE:
            return
        self.theShapeProperty.updateShapeProperty()

    def destroy( self, *arg ):
        """destroy dialog
        """
        pass        
        
    def selectEntity( self, anEntityList ):
        objects = self.theObjectDict.values() 
        if not len(objects) == 1:
            return
        theObject = objects[0]
        if not theObject.getProperty(OB_PROP_HAS_FULLID):
            return
        selectedFullID = theObject.getProperty( OB_PROP_FULLID )
        selectedEntity = self.theModelEditor.getModel().getEntity( selectedFullID )
        if selectedEntity == None:
            return
        self.theLastDisplayedEntity = selectedEntity
        self.theEntityEditor.setDisplayedEntity( selectedEntity )
        self.theEntityEditor.update()
        self.bringToTop()
