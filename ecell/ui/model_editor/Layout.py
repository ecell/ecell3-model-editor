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
import math
import ecell.util
from ecell.model.store import *

from ecell.ui.model_editor.Constants import *
from ecell.ui.model_editor.PackingStrategy import PackingStrategy

import ecell.ui.model_editor.viewobjects as viewobjs
import ecell.ui.model_editor.Utils as utils

__all__ = (
    'Layout'
    )

DEFAULT_SCROLL_REGION = ( -1000, -1000, 1000, 1000 )

class PackingStrategy:
    angleMatrix = (
        ( RING_RIGHT,  RING_LEFT   ),
        ( RING_TOP,    RING_BOTTOM ),
        ( RING_LEFT,   RING_RIGHT  ),
        ( RING_BOTTOM, RING_TOP    )
        )

    def __init__( self, aLayout ):
        self.layout = aLayout

    def autoMoveObject( self, systemFullID, objectID ):
        # return cmdlist: delete or move + resize command
        cmdList = []
        # get Object of systemFullID
        systemList = self.layout.getObjectList( OB_PROP_TYPE_SYSTEM )
        systemObject = None
        for aSystemObject in systemList:
            if aSystemObject.getProperty( OB_PROP_FULLID ) == systemFullID:
                systemObject = aSystemObject
                break
        if systemObject == None:
            # create delete command
            delCmd = DeleteObject ( self.layout, objectID )
            cmdList.append( delCmd )
        else:
            anObject = self.layout.getObject( objectID )
            # get dimensions of object
            objectWidth = anObject.getProperty( OB_PROP_DIMENSION_X )
            objectHeigth = anObject.getProperty( OB_PROP_DIMENSION_Y )
            
            # get inside dimensions of system
            systemWidth = systemObject.getProperty ( SY_INSIDE_DIMENSION_X )
            systemHeigth = systemObject.getProperty ( SY_INSIDE_DIMENSION_Y )

            # resize if necessary
            resizeNeeded = False
            oldObjectWidth = objectWidth
            oldObjectHeigth = objectHeigth
            if objectWidth >= systemWidth:
                resizeNeeded = True
                objectWidth = systemWidth /2
                if objectWidth < OB_MIN_WIDTH:
                    objectWidth = OB_MIN_WIDTH
        
            
            if objectHeigth >= systemHeigth:
                resizeNeeded = True
                objectHeigth = systemHeigth /2
                if objectHeigth < OB_MIN_HEIGTH:
                    objectHeigth = OB_MIN_HEIGTH

            if resizeNeeded:
                cmdList.append( ResizeObject( self.layout, objectID, 0, objectHeigth - oldObjectHeigth, 0, objectWidth - oldObjectWidth ) )
            # get rnd coordinates
            leewayX = systemWidth - objectWidth
            leewayY = systemHeigth - objectHeigth
            import random
            rGen = random.Random(leewayX)
            posX = rGen.uniform(0,leewayX)
            posY = rGen.uniform(0,leewayY)

            # create cmd
            cmdList.append( MoveObject( self.layout, objectID, posX, posY, systemObject ) )

        return cmdList

    def autoConnect( self, processObjectID, variableObjectID ):
        # source and target can be in a form of ( centerx, centery), too

        
        # get dimensions of object and x, y pos
        if type(processObjectID) in ( type(()), type([] ) ):
            aProObjectXCenter, aProObjectYCenter = processObjectID
        else:
            aProObject = self.layout.getObject( processObjectID )
            aProObjectWidth = aProObject.getProperty( OB_PROP_DIMENSION_X )
            aProObjectHeigth = aProObject.getProperty( OB_PROP_DIMENSION_Y )
            (aProObjectX1,aProObjectY1)=aProObject.getAbsolutePosition()
            aProObjectXCenter = aProObjectX1 + aProObjectWidth/2
            aProObjectYCenter = aProObjectY1 + aProObjectHeigth/2

        if type(variableObjectID) in ( type(()), type([] ) ):
            aVarObjectXCenter, aVarObjectYCenter = variableObjectID
        else:
            aVarObject = self.layout.getObject( variableObjectID )
            aVarObjectWidth = aVarObject.getProperty( OB_PROP_DIMENSION_X )
            aVarObjectHeigth = aVarObject.getProperty( OB_PROP_DIMENSION_Y )
            (aVarObjectX1,aVarObjectY1)=aVarObject.getAbsolutePosition()
            aVarObjectXCenter = aVarObjectX1 +aVarObjectWidth/2
            aVarObjectYCenter = aVarObjectY1 +aVarObjectHeigth/2

        #assign process ring n var ring
        return self.getRings( aProObjectXCenter, aProObjectYCenter, aVarObjectXCenter, aVarObjectYCenter )
        
    def createEntity( self, anEntityType, x, y ):
        # return command for entity and center
        # get parent system
        parentSystem = self.layout.getSystemAtXY( x, y )
        if parentSystem == None:
            return
        if anEntityType == DM_TYPE_SYSTEM:
            buttonType = PE_SYSTEM
        elif anEntityType == DM_TYPE_PROCESS:
            buttonType = PE_PROCESS
        elif anEntityType == DM_TYPE_VARIABLE:
            buttonType = PE_VARIABLE
        else:
            return None, 0, 0
        #get relcords
        command, width, height = parentSystem.createObject( x, y , buttonType )
        
        return  command,  width, height

    def autoShowObject( self, aFullID ):
        # return cmd or comes up with error message!
        pass
        
    def getRings( self, x0, y0, x1, y1 ):
        # return sourcering, targetring
        dy = y0-y1; dx = x1-x0;
        if dx == 0:
            dx = 0.0001
        if dy == 0:
            dy = 0.0001
        
        angle = math.atan( dy/dx )/math.pi*180
        if angle < 0:
            angle +=180
        if dy <0:
            angle += 180
        idx = int(angle/90 +0.5)%4
        return self.angleMatrix[idx]
        
class Layout( viewobjs.EditorObject ):
    def __init__( self, layoutManager, layoutBufferFactory, objectID ):
        EditorObject.__init__( self, None, objectID, None )
        self.theCounter = 0
        self.layoutManager = layoutManager
        self.layoutBufferFactory = layoutBufferFactory
        self.theName = aName
        self.idToObjectMap = {}
        self.fullIDToObjectMap = {}
        self.thePropertyMap = {}
        self.orgScrollRegion = DEFAULT_SCROLL_REGION
        self.thePropertyMap[ OB_PROP_DIMENSION_X ] = default_scrollregion[2] - default_scrollregion[0]
        self.thePropertyMap[ OB_PROP_DIMENSION_Y ] = default_scrollregion[3] - default_scrollregion[1]

        default_zoomratio = 1
        self.thePropertyMap[ LO_SCROLL_REGION ] = default_scrollregion
        self.thePropertyMap[ LO_ZOOM_RATIO ] = default_zoomratio
        self.theCanvas = None
        self.thePathwayEditor = None
        self.theSelectedObjectIDList = []
        

        # always add root dir object
        anObjectID = self.getUniqueObjectID( OB_PROP_TYPE_SYSTEM )
        self.createObject(
            anObjectID, OB_PROP_TYPE_SYSTEM, identifiers.ROOT_SYSTEM_FULLID,
            default_scrollregion[0], default_scrollregion[1], None )
        self.theRootObject = self.getObject( anObjectID )
        
        self.thePropertyMap[ LO_ROOT_SYSTEM ] = anObjectID
        
    def update( self, aType = None, anID = None ):
        # i am not sure this is necessary
        pass

    def isShown( self ):
        return self.theCanvas != None

    def getName(self):
        return self.theName

    def getLayoutManager(self):
        return self.layoutManager

    def getPathwayEditor(self):
        return self.thePathwayEditor 

    def attachToCanvas( self, aCanvas ):
        self.theCanvas = aCanvas
        self.thePathwayEditor = self.theCanvas.getParentWindow()
        self.theCanvas.setLayout( self )
        # set canvas scroll region
        scrollRegion = self.getProperty( LO_SCROLL_REGION )
        self.theCanvas.setSize( scrollRegion )
        # set canvas ppu
        ppu = self.getProperty( LO_ZOOM_RATIO )
        self.theCanvas.setZoomRatio( ppu )
        self.theCanvas.scrollTo( scrollRegion[0], scrollRegion[1],'attach')
        # set canvas for objects and show objects

        self.__showObject( self.thePropertyMap[ LO_ROOT_SYSTEM ] )
        # then get all the connections, setcanvas, show
        for objectID in self.getObjectList( OB_PROP_TYPE_CONNECTION ):
            anObject = self.idToObjectMap[ objectID ]
            anObject.setCanvas( self.theCanvas )
            anObject.show()
        self.resumeSelection()
        
    def __showObject( self, anObjectID ):
        anObject = self.idToObjectMap[ anObjectID ]
        anObject.setCanvas( self.theCanvas )
        anObject.show()
        if anObject.getProperty( OB_PROP_TYPE ) == OB_PROP_TYPE_SYSTEM:
            objectList = anObject.getObjectList()
            for anID in objectList:
                self.__showObject( anID )

    def detachFromCanvas( self ):
        
        # hide objects and setcanvas none
        for objectID in self.idToObjectMap.keys():
            anObject = self.idToObjectMap[ objectID ]
            anObject.setCanvas( None )
            anObject.hide()

        self.theCanvas = None

    def getCanvas( self ):
        return self.theCanvas

    def rename( self, newName ):
        self.theName = newName
        if self.thePathwayEditor!=None:
            self.thePathwayEditor.update()
        
    def __checkCounter ( self, objectID ):
        i=len(objectID) -1
        while not objectID[:i].isalpha():
            i-=1
        oid = long(objectID[i:])
        if oid> self.theCounter:
            self.theCounter = oid

    def createObject( self, objectID, objectType, aFullID=None, x=None, y=None, parentSystem = None  ):
        assert aFullID == None or isinstance( aFullID, identifiers.FullID )
        if parentSystem == None:
            parentSystem = self
        # object must be within a system except for textboxes 
        # parentSystem object cannot be None, just for root
        self.__checkCounter( objectID )
        if x == None and y == None:
            (x,y) = parentSystem.getEmptyPosition()

        if objectType == OB_PROP_TYPE_PROCESS:
            assert aFullID != None
            newObject = viewobjs.ProcessObject( self, objectID, parentSystem, x, y, aFullID )
        elif objectType == OB_PROP_TYPE_VARIABLE:
            assert aFullID != None
            newObject = viewobjs.VariableObject( self, objectID, parentSystem, x, y, aFullID )
        elif objectType == OB_PROP_TYPE_SYSTEM:
            assert aFullID != None
            newObject = viewobjs.SystemObject( self, objectID, parentSystem, x, y, aFullID )
        elif objectType == OB_PROP_TYPE_TEXT:
            newObject = viewobjs.TextObject( self, objectID, parentSystem, x, y )
        elif objectType == OB_PROP_TYPE_CONNECTION:
            raise "Connection object cannot be created via Layout.createObject"
        else:
            raise Exception("Object type %s does not exists"%objectType)

        if aFullID != None:
            self.fullIDToObjectMap[ aFullID ] = newObject

        self.idToObjectMap[ objectID ] = newObject
        if self.theCanvas!=None:
            newObject.setCanvas( self.theCanvas )
            newObject.show()
            self.selectRequest( objectID )

    def deleteObject( self, anObjectID ):
        #unselect
        if  anObjectID in self.theSelectedObjectIDList:
            self.theSelectedObjectIDList.remove( anObjectID )
        anObject = self.getObject( anObjectID )
        aParent = anObject.getParent()
        anObject.destroy()
        if aParent != self:
            aParent.unregisterObject( anObjectID )
        self.idToObjectMap.__delitem__( anObjectID )

    def getObjectList( self, anObjectType = None ):
        # returns IDs
        if anObjectType == None:
            return self.idToObjectMap.keys()
        returnList = []
        for anID in self.idToObjectMap.keys():
            anObject = self.idToObjectMap[ anID ]
            if anObject.getProperty( OB_PROP_TYPE ) == anObjectType:
                returnList.append( anID )
        return returnList

    def getObjectByFullID( self, fullID ):
        return self.fullIDToObjectMap[ fullID ]

    def getPropertyList( self ):
        return self.thePropertyMap.keys()
    
    def getProperty( self, aPropertyName ):
        if aPropertyName in self.thePropertyMap.keys():
            return self.thePropertyMap[aPropertyName]
        else:
            raise Exception("Unknown property %s for layout %s"%(self.theName, aPropertyName ) )

    def setProperty( self, aPropertyName, aValue ):
        self.thePropertyMap[aPropertyName] = aValue
        if aPropertyName==LO_SCROLL_REGION:
            scrollRegion=self.getProperty(LO_SCROLL_REGION)
            self.thePropertyMap[ OB_PROP_DIMENSION_X ]=scrollRegion[2]-scrollRegion[0]
            self.thePropertyMap[ OB_PROP_DIMENSION_Y ]=scrollRegion[3]-scrollRegion[1]
            if self.theCanvas!=None:
                self.theCanvas.setSize( scrollRegion )
            
    def getAbsoluteInsidePosition( self ):
        return ( 0, 0 )

    def moveObject(self, anObjectID, newX, newY, newParent ):
        # if newParent is None, means same system
        # currently doesnt accept reparentation!!!
        anObject = self.getObject( anObjectID )
        deltax = newX - anObject.getProperty( OB_PROP_POS_X ) 
        deltay = newY - anObject.getProperty( OB_PROP_POS_Y )
        anObject.move( deltax, deltay )

    def getObject( self, anObjectID ):
        # returns the object including connectionobject
        if anObjectID not in self.idToObjectMap.keys():
            raise Exception("%s objectid not in layout %s"%(anObjectID, self.theName))
        return self.idToObjectMap[ anObjectID ]

    def resizeObject( self, anObjectID, deltaTop, deltaBottom, deltaLeft, deltaRight ):
        # inward movement negative, outward positive
        anObject = self.getObject( anObjectID )
        anObject.resize( deltaTop, deltaBottom, deltaLeft, deltaRight )

    def createConnectionObject( self, anObjectID, aProcessObjectID = None, aVariableObjectID=None,  processRing=None, variableRing=None, direction = PROCESS_TO_VARIABLE, aVarrefName = None ):
        self.__checkCounter( anObjectID )
        # if processobjectid or variableobjectid is None -> no change on their part
        # if process or variableID is the same as connection objectid, means that it should be left unattached
        # direction is omitted
        newObject = viewobjs.ConnectionObject( self, anObjectID, self, aVariableObjectID, aProcessObjectID, variableRing, processRing, aVarrefName )
        
        self.idToObjectMap[ anObjectID ] = newObject
        if self.theCanvas!=None:
            newObject.setCanvas( self.theCanvas )
            newObject.show()
            self.selectRequest( anObjectID )

    def redirectConnectionObject( self, anObjectID, newProcessObjectID, newVariableObjectID = None, processRing = None, variableRing = None, varrefName =None ):
        # if processobjectid or variableobjectid is None -> no change on their part
        # if process or variableID is the same as connection objectid, means that it should be left unattached
        conObject = self.getObject( anObjectID )
        conObject.redirectConnbyComm(newProcessObjectID,newVariableObjectID,processRing,variableRing,varrefName)

    def userMoveObject( self, ObjectID, deltaX, deltaY ):
        #to be called after user releases shape
        pass
        #return TRUE move accepted, FALSE move rejected

    def userCreateConnection( self, aProcessObjectID, startRing, targetx, targety ):
        pass
        #return TRUE if line accepted, FALSE if line rejected

    def autoAddSystem( self, aFullID ):
        pass

    def autoAddEntity( self, aFullID ):
        pass

    def autoConnect( self, aProcessFullID, aVariableFullID ):
        pass

    def getUniqueObjectID( self, anObjectType ):
        # objectID should be string
        self.theCounter += 1
        return "%s%d" % ( anObjectType, self.theCounter )

    def getName( self ):
        return self.theName

    def graphUtils( self ):
        return self.layoutManager.theModelEditor.theGraphicalUtils

    def popupObjectEditor( self, anObjectID ):
        anObject = self.getObject( anObjectID )
        if anObject.getProperty(OB_PROP_TYPE) == OB_PROP_TYPE_CONNECTION:
            self.layoutManager.theModelEditor.createConnObjectEditorWindow(self.theName, anObjectID)
        else:
            if  anObject.getProperty(OB_PROP_HAS_FULLID): 
                self.layoutManager.theModelEditor.createObjectEditorWindow(self.theName, anObjectID)
            else:
                utils.showPopupMessage(
                    utils.OK_MODE,
                    "Sorry, not implemented!",
                    ME_ERROR )

    def getPaletteButton( self ):
        return self.thePathwayEditor.getPaletteButton()

    def registerObject( self, anObject ):
        pass

    def selectRequest( self, objectID , shift_press = False ):
        anObject = self.getObject( objectID )
        if len( self.theSelectedObjectIDList ) == 0:
            selectedType = None
        else:
            selectedType = self.getObject( self.theSelectedObjectIDList[0] ).getProperty( OB_PROP_TYPE )

        objectType = self.getObject(objectID ).getProperty(OB_PROP_TYPE )
            
        selectedObjectID = objectID
        multiSelectionAllowed = False
        if shift_press == False:
            #if shift_press == False: 
            for anID in self.theSelectedObjectIDList:
                self.getObject( anID ).unselected()
            self.theSelectedObjectIDList = []
        elif len( self.theSelectedObjectIDList ) > 0:
            if selectedType == OB_PROP_TYPE_CONNECTION:
                selectionSystemPath = None
            else:
                selectionSystemPath = self.getObject( self.theSelectedObjectIDList[0] ).getProperty( OB_PROP_FULLID ).split(':')[1]
            if objectType == OB_PROP_TYPE_CONNECTION:
                objectSystemPath  = None
            else:
                objectSystemPath = anObject.getProperty( OB_PROP_FULLID ).split(':')[1]
            multiSelectionAllowed = ( selectionSystemPath == objectSystemPath )
        else:
            multiSelectionAllowed = True

        if anObject.isSelected and shift_press:
            self.theSelectedObjectIDList.remove( objectID )
            anObject.unselected()
            if len(self.theSelectedObjectIDList) == 0:
                selectedObjectID = None
            else:
                selectedObjectID = self.theSelectedObjectIDList[-1]
        else:        
            if len(self.theSelectedObjectIDList)> 0:
                if shift_press and multiSelectionAllowed :
                    self.theSelectedObjectIDList += [objectID]
                    anObject.selected()
                else:
                    return
            else:
                self.theSelectedObjectIDList += [objectID]
                anObject.selected()
        
        if objectType == OB_PROP_TYPE_CONNECTION:
            self.layoutManager.theModelEditor.createConnObjectEditorWindow( self.theName, self.theSelectedObjectIDList )
        else:
            self.layoutManager.theModelEditor.createObjectEditorWindow( self.theName, self.theSelectedObjectIDList )
            
    def deleteEntities( self ):
        aModelEditor = self.layoutManager.theModelEditor
        aCommandList = []

        for anObjectID in self.theSelectedObjectIDList:
            anObject = self.getObject( anObjectID )
            if anObject.getProperty( OB_PROP_HAS_FULLID ):
                aFullID  = anObject.getProperty( OB_PROP_FULLID )
                aCommandList += [ DeleteEntityList( aModelEditor, [ aFullID ] ) ]

            elif anObject.getProperty( OB_PROP_TYPE )==OB_PROP_TYPE_CONNECTION:
                connObj = anObject
                varreffName = connObj.getProperty(CO_NAME)
                proID = connObj.getProperty(CO_PROCESS_ATTACHED)
                aProcessObject = self.getObject(proID)
                aProcessFullID = aProcessObject.getProperty( OB_PROP_FULLID )
                fullPN = aProcessFullID+':' +MS_PROCESS_VARREFLIST
                aVarReffList = ecell.util.copyValue(
                    aModelEditor.theModel.getEntityProperty( fullPN ) )[:]

                for aVarref in aVarReffList:
                    if aVarref[ME_VARREF_NAME] == varreffName :
                        aVarReffList.remove( aVarref )
                        break
                aCommandList += [ ChangeEntityProperty( aModelEditor, fullPN, aVarReffList ) ]
        self.passCommand(  aCommandList  )

    def deleteSelected( self ):
        aCommandList = []
        for anObjectID in self.theSelectedObjectIDList:
            aCommandList += [ DeleteObject( self, anObjectID ) ]
        self.passCommand( aCommandList )
                
    def resumeSelection( self ):
        for anID in self.theSelectedObjectIDList:
            anObject = self.getObject( anID )
            anObject.selected()
        
    def checkConnection( self, x, y, checkFor ):
        objectIDList = self.getObjectList( checkFor )
        for anObjectID in objectIDList:
            anObject = self.idToObjectMap[ anObjectID ]
            (objx1, objy1) = anObject.getAbsolutePosition()
            if x< objx1 - 3 or y < objy1 - 3:
                continue
            objx2 = objx1 + anObject.getProperty( OB_PROP_DIMENSION_X )
            objy2 = objy1 + anObject.getProperty( OB_PROP_DIMENSION_Y )

            if x > 3 + objx2 or y > 3 + objy2:
                continue
            rsize = anObject.getRingSize()
            chosenRing = None
            chosenDist = None
            for aRingName in [ RING_TOP, RING_BOTTOM, RING_LEFT, RING_RIGHT ]:
                (rx, ry) = anObject.getRingPosition( aRingName )
                distance = math.sqrt((rx-x)**2+(ry-y)**2)
                if chosenDist == None or chosenDist>distance:
                    chosenDist = distance
                    chosenRing = aRingName
                    
            return ( anObjectID, chosenRing )
        return ( None, None )
        
    def getSystemAtXY( self, x, y ):
        # return systemID at absolute position
        return self.theRootObject.getSystemAtXY( x, y)
