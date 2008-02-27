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
import gtk

import os
import os.path
import string

from ListWindow import ListWindow
from ClassEditor import ClassEditor
from ClassList import ClassList
from Constants import *

class ClassEditorWindow(ListWindow):
    def __init__( self, aModelEditor, aRoot = 'top_frame' ):
        """
        in: ModelEditor theModelEditor
        returns nothing
        """
        ListWindow.__init__( self, aModelEditor )
        self.initUI()

    def initUI( self ):
        """
        in: nothing
        returns nothing
        """
        # superclass openwindow
        ListWindow.initUI( self )

        # add stepperlist
        self.theClassList = ClassList( self, self['ClassListFrame'] )

        # add stepperpropertylist
        self.theClassPropertyList = ClassEditor( self, self['ClassPropertyFrame'] )

        # add signal handlers
        # self.addHandlers({  })
        self.theClassList.update()
        classList = self.theModelEditor.getModel().getStepperList()
        if len(classList) == 0:
            aClassList = []
        else:
            aClassList = [ classList[0] ]
        self.selectStepper( aClassList )

    def updateEntityList ( self ):
        if not self.exists():
            return
        self.theClassList.update(  )

        self.updatePropertyList( )



    def updatePropertyList ( self, anID = None ):
        """
        in: anID ( system or stepper ) where changes happened
        """
        
        if not self.exists():
            return
        oldDisplayedID = self.theClassPropertyList.getDisplayedStepper()

        selectedIDs = self.theClassList.getSelectedIDs()
        if len( selectedIDs) != 1:
            newDisplayedID =  None
        else:
            newDisplayedID = selectedIDs[0]

        if oldDisplayedID != newDisplayedID or newDisplayedID == anID or anID == None:
            self.theClassPropertyList.setDisplayedStepper( newDisplayedID )


    def setLastActiveComponent( self, aComponent ):
        pass
            

    def update( self, aType = None, anID = None ):
        # anID None means all for steppers
        if aType == DM_STEPPER_TYPE:
            if anID == None:
                # update all
                self.updateEntityList()
            else:
                self.updatePropertyList( anID )

        elif aType in [ DM_SYSTEM_TYPE, DM_PROCESS_TYPE, None]:
            self.updatePropertyList()
        elif aType == DM_PROPERTY_TYPE:
            self.updatePropertyList( anID )


    def selectStepper( self, aStepperList ):
        self.theClassList.changeSelection( aStepperList )
        self.theClassList.selectByUser()



    #############################
    #      SIGNAL HANDLERS      #
    #############################

    def deleted( self, *args ):
        ListWindow.deleted( self, *args )
        self.theClassList.close()
        self.theClassPropertyList.close()
        self.theModelEditor.theClassEditor = None
        self.theModelEditor.theMainWindow.update()
        return True


