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

from ModelEditor import *
from ListWindow import *
import os
import os.path
import string

from StepperEditor import *
from StepperList import *
from Constants import *


class StepperTab(ListWindow):
    def __init__( self, aModelEditor, aRoot = 'top_frame' ):
        """
        in: ModelEditor theModelEditor
        returns nothing
        """
        ListWindow.__init__( self, aModelEditor, aRoot )
        self.initUI()

    def initUI( self ):
        """
        in: nothing
        returns nothing
        """
        # superclass openwindow
        ListWindow.initUI( self )
        
        # add stepperlist
        self.theStepperList = StepperList( self, self['StepperListFrame'] )

        # add stepperpropertylist
        self.theStepperPropertyList = StepperEditor( self, self['PropertyListFrame'] )
        #self.theRoot='top_frame'
        # add signal handlers
        # self.addHandlers({  })
        self.theStepperList.update()
        stepperList = self.theModelEditor.getModel().getStepperList()
        if len(stepperList) == 0:
            aStepperList = []
        else:
            aStepperList = [ stepperList[0] ]
        self.selectStepper( aStepperList )

    def updateEntityList ( self ):
        if not self.exists():
            return
        self.theStepperList.update(  )

        self.updatePropertyList( )



    def updatePropertyList ( self, anID = None ):
        """
        in: anID ( system or stepper ) where changes happened
        """
        
        if not self.exists():
            return
        oldDisplayedID = self.theStepperPropertyList.getDisplayedStepper()

        selectedIDs = self.theStepperList.getSelectedIDs()
        if len( selectedIDs) != 1:
            newDisplayedID =  None
        else:
            newDisplayedID = selectedIDs[0]

        if oldDisplayedID != newDisplayedID or newDisplayedID == anID or anID == None:
            self.theStepperPropertyList.setDisplayedStepper( newDisplayedID )


    def setLastActiveComponent( self, aComponent ):
        pass
            

    def update( self, aType = None, anID = None ):
        # anID None means all for steppers
        #if self.theModelEditor.getMode() == ME_RUN_MODE:
        #    self.theStepperPropertyList.thePropertyList.update()
        #    return
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
        self.theStepperList.changeSelection( aStepperList )
        self.theStepperList.selectByUser()



    #############################
    #      SIGNAL HANDLERS      #
    #############################

    def deleted( self, *args ):
        ListWindow.deleted( self, *args )
        self.theStepperList.close()
        self.theStepperPropertyList.close()
        self.theModelEditor.theMainWindow.update()
        self.theModelEditor.theStepperWindowList.remove( self )
        return True


