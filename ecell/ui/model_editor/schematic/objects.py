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

from sets import Set

from ecell.event import Event, EventDispatcher
import ecell.util
import ecell.identifiers as identifiers

import ecell.ui.model_editor.shape as shape
import ecell.ui.model_editor.Utils as utils

__all__ = (
    'ViewObjectEvent',
    'EditorObject',
    'SystemObject',
    'ProcessObject',
    'VariableObject',
    'ConnectionObject',
    'TextObject'
    )

OB_SHOW_LABEL = 1

class GhostLine:
    def __init__( self, parentObject, ringCode, endx, endy ):
        self.parentObject = parentObject
        self.x2 = endx
        self.y2 = endy
        (self.x1, self.y1) = self.parentObject.getRingPosition( ringCode )
        self.root = self.parentObject.theCanvas.getCanvas().root()
        self.theLine = self.root.add( gnomecanvas.CanvasLine, points = (self.x1, self.y1, self.x2, self.y2), last_arrowhead = True,arrow_shape_a = 5, arrow_shape_b = 5, arrow_shape_c = 3, fill_color = 'black' )

    def moveEndPoint( self, dx, dy ):
        if self.parentObject.outOfRoot( self.x2 + dx, self.y2 + dy ):
            return
        self.x2 += dx
        self.y2 += dy
        self.theLine.set_property( "points", (self.x1, self.y1, self.x2, self.y2) )

    def getEndPoint( self ):
        return ( self.x2, self.y2 )

    def registerObject( self, anObject ):
        self.theObjectMap[anObject.getID()] = anObject

    def unregisterObject ( self, anObjectID ):
        self.theObjectMap.__delitem__( anObjectID )

    def delete ( self ):
        self.theLine.dispose()

class ConcreteObject( EditorObject ):
    def __init__( self, aLayout, objectID, parentObject, x, y ):
        EditorObject.__init__( self, aLayout, objectID, parentObject )
        self.properties[ OB_PROP_POS_X ] = x
        self.properties[ OB_PROP_POS_Y ] = y
        self.theShape = None

    def dispose( self ):
        if self.theShape != None:
            self.theShape.delete()

    def getShapeDescriptor( self, aShapeName ):
        graphUtils =  self.layout.graphUtils()
        theLabel = self.getProperty( OB_PROP_LABEL )
        aShapeType = self.getProperty( OB_PROP_TYPE )
        if aShapeName == aShapeType:
            aShapeName = OB_PROP_TYPE_DEFAULT
        return self.ShapePluginManager.createShapePlugin(
            aShapeType,aShapeName,self, graphUtils, theLabel )

    def selected( self ):
        if not self.isSelected:
            self.isSelected = True
            self.theShape.selected()
            self.theShape.outlineColorChanged()

    def unselected( self ):
        if self.isSelected:
            self.isSelected = False
            self.theShape.unselected()
            self.theShape.outlineColorChanged()

    def setProperty( self, aPropertyName, aPropertyValue):
        EditorObject.setProperty( self, aPropertyName, aPropertyValue )
        if aPropertyName == OB_PROP_LABEL:
            self.theSD.renameLabel(aPropertyValue)
        elif aPropertyName in ( OB_PROP_DIMENSION_X, OB_PROP_DIMENSION_Y ):
            self.theSD.reCalculate()
        elif aPropertyName == OB_PROP_SHAPE_TYPE :
            anSD = self.getShapeDescriptor( aPropertyValue )
            self.setShapeDescriptor( anSD )
        if  self.theCanvas  != None:
            if aPropertyName == OB_PROP_LABEL:
                self.labelChanged(aPropertyValue)
            elif aPropertyName == OB_PROP_TEXT_COLOR :
                self.theShape.outlineColorChanged()
            elif aPropertyName == OB_PROP_OUTLINE_COLOR:
                self.theShape.outlineColorChanged()
            elif aPropertyName == OB_PROP_FILL_COLOR:
                self.theShape.fillColorChanged()

    def show( self ):
        self.theShape = ComplexShape(
            self,
            self.theCanvas,
            self.properties[ OB_PROP_POS_X ],
            self.properties[ OB_PROP_POS_Y ],
            self.properties[ OB_PROP_DIMENSION_X ],
            self.properties[ OB_PROP_DIMENSION_Y ] )
        self.theShape.show()

    def setShapeDescriptor( self, anSD ):
        if self.theCanvas != None and self.theShape != None:
            self.theShape.delete()
        self.theSD = anSD
        self.properties[OB_PROP_SHAPE_DESCRIPTOR_LIST] = self.theSD
        
        if self.theCanvas != None:
            self.theShape.show()

    def move( self, dx, dy ):
        self.properties[ OB_PROP_POS_X ] += dx
        self.properties[ OB_PROP_POS_Y ] += dy
        if self.theShape != None:
            self.theShape.move( dx, dy )

    def parentMoved( self, dx, dy ):
        # no change in relative postions
        self.theShape.move( dx, dy )

    def objectDragged( self, dx, dy ):
        cmdList = []
        theParent = self.parentObject
        if isinstance( theParent, Layout ):
            #rootsystem cannot be moved!!!
            return
        if self.theShape.getFirstDrag() and not self.theShape.getDragBefore() :
            self.rn = self.createRnOut()
            # store org position first
            self.ox= self.getProperty( OB_PROP_POS_X )
            self.oy= self.getProperty( OB_PROP_POS_Y )
            # for parent
            theParent.thex1org = theParent.properties[OB_PROP_POS_X]
            theParent.they1org = theParent.properties[OB_PROP_POS_Y]
            theParent.thex2org = theParent.thex1org+theParent.properties[OB_PROP_DIMENSION_X]
            theParent.they2org = theParent.they1org+theParent.properties[OB_PROP_DIMENSION_Y]
            #for Layout
            self.layout.orgScrollRegion = self.layout.getProperty( LO_SCROLL_REGION )
            self.theShape.setFirstDrag(False)
            self.theShape.setDragBefore(True)
            

        if self.theShape.getIsButtonPressed(): 
            newx = self.getProperty( OB_PROP_POS_X ) + dx
            newy = self.getProperty( OB_PROP_POS_Y ) + dy

            if newx ==0 and newy == 0:
                return
            # get self's newx2,newy2
            newx2 = newx+self.getProperty(OB_PROP_DIMENSION_X)
            newy2 = newy+self.getProperty(OB_PROP_DIMENSION_Y)
            rpar = self.createRparent()
            if not self.isWithinParent(newx,newy,newx2,newy2,rpar):
                dir = self.getDirectionShift(dx,dy)
                UDLR = theParent.getUDLRmatrix(dx,dy,dir)
                deltaup = UDLR[theParent.UDLRMap['U']]
                deltadown = UDLR[theParent.UDLRMap['D']]
                deltaright = UDLR[theParent.UDLRMap['R']]
                deltaleft = UDLR[theParent.UDLRMap['L']]
                delta = theParent.getDelta(UDLR)
                
                if isinstance( theParent.theparentObject, Layout ):
                    self.adjustLayoutCanvas(
                        deltaup, deltadown, deltaleft, deltaright )
                    theParent.resize(
                        deltaup, deltadown, deltaleft, deltaright )
                else:
                    if dir in [DIRECTION_RIGHT,DIRECTION_UP,DIRECTION_DOWN,DIRECTION_LEFT]:
                        maxShift = theParent.getMaxShiftPos(dir)
                        if maxShift>0:
                            if maxShift>delta:              
                                theParent.resize(   deltaup, deltadown, deltaleft, deltaright )
                                self.adjustCanvas(dx,dy)
                            else:
                                return
                    else:
                        maxShiftx,maxShifty = theParent.getMaxShiftPos(dir)
                        if maxShiftx>0 and maxShifty>0:
                            if maxShiftx>delta and maxShifty>delta:         
                                theParent.resize(   deltaup, deltadown, deltaleft, deltaright )
                                self.adjustCanvas(dx,dy)
                            else:
                                return
                
            else: # stays within parent
                if self.isOverlap(newx,newy,newx2,newy2,self.rn):   
                    return                      
                else:           
                    self.move(dx,dy)
                    self.adjustCanvas(dx,dy)
        else: # button release
            # for self
            self.lastx = self.properties[ OB_PROP_POS_X ]
            self.lasty = self.properties[ OB_PROP_POS_Y ]
            newx = self.lastx
            newy = self.lasty
            self.move(-(self.getProperty( OB_PROP_POS_X )-self.ox) ,-(self.getProperty( OB_PROP_POS_Y )-self.oy))
            self.properties[ OB_PROP_POS_X ] =self.ox
            self.properties[ OB_PROP_POS_Y ] =self.oy

            # create command for self
            aCommand1 = lcmds.MoveObject( self.layout, self.id, newx, newy, None )
            cmdList.append(aCommand1)

            # parent
            theParent.thedleftorg = theParent.properties[OB_PROP_POS_X]-theParent.thex1org
            theParent.thedrightorg = theParent.properties[OB_PROP_POS_X]+theParent.properties[OB_PROP_DIMENSION_X]-theParent.thex2org
            theParent.theduporg = theParent.properties[OB_PROP_POS_Y]-theParent.they1org
            theParent.theddownorg = theParent.properties[OB_PROP_POS_Y]+theParent.properties[OB_PROP_DIMENSION_Y]-theParent.they2org
            revCom2 = theParent.resize( theParent.theduporg, -theParent.theddownorg, theParent.thedleftorg, -theParent.thedrightorg )
            
            #create command for parent
            aCommand2 = lcmds.ResizeObject( theParent.layout, theParent.id, -theParent.theduporg, theParent.theddownorg, -theParent.thedleftorg, theParent.thedrightorg )
            #aCommand2.makeExecuted( [revCom2] )
            cmdList.append(aCommand2)
            

            # Layout
            newScrollRegion = self.layout.getProperty(LO_SCROLL_REGION)
            self.layout.setProperty(LO_SCROLL_REGION,self.layout.orgScrollRegion)
            #self.layout.setProperty(OB_PROP_DIMENSION_X,self.layout.orgScrollRegion[2]-self.layout.orgScrollRegion[0])
            #self.layout.setProperty(OB_PROP_DIMENSION_Y,self.layout.orgScrollRegion[3]-self.layout.orgScrollRegion[1])
            self.layout.getCanvas().setSize(self.layout.orgScrollRegion)
            #create command for Layout
            
            aCommand3 = lcmds.ChangeLayoutProperty(self.layout, LO_SCROLL_REGION,newScrollRegion)
            revCom3 = lcmds.ChangeLayoutProperty( self.layout, LO_SCROLL_REGION, self.layout.orgScrollRegion )
            #aCommand3.makeExecuted([revCom3])
            cmdList.append(aCommand3)
            self.layout.passCommand( cmdList)
            lastposx,lastposy = self.layout.getCanvas().getLastCursorPos()
            if self.layout.orgScrollRegion != newScrollRegion:
                self.layout.getCanvas().scrollTo(lastposx,lastposy,'attach')

    def getAbsolutePosition( self ):
        ( xpos, ypos ) = self.parentObject.getAbsoluteInsidePosition()
        return ( xpos + self.properties[ OB_PROP_POS_X ], ypos + self.properties[ OB_PROP_POS_Y ])

    def outOfRoot( self, x, y ):
        rootSystemID = self.layout.getProperty( LO_ROOT_SYSTEM )
        rootSystem = self.layout.getObject ( rootSystemID )
        rx1 = rootSystem.getProperty( OB_PROP_POS_X ) + 3
        ry1 = rootSystem.getProperty ( OB_PROP_POS_Y ) + 20
        rx2 = rx1 + rootSystem.getProperty( SY_INSIDE_DIMENSION_X )
        ry2 = ry1 + rootSystem.getProperty( SY_INSIDE_DIMENSION_Y )
        if x<rx1 or x>rx2 or y<ry1 or y>ry2:
            return True
        return False

class EntityObject( ConcreteObject ):
    def __init__( self, aLayout, objectID, parentObject, x, y, fullID ):
        ConcreteObject.__init__( self, aLayout, objectID, parentObject, x, y )
        self.properties[ OB_PROP_HAS_FULLID ] = True
        self.properties[ OB_PROP_FULLID ] = fullID

    def getDMType():
        return None

    def __extend_label(self,*args):
        aLabel = self.getProperty(OB_PROP_LABEL)
        oldLen = len(aLabel)
        aFullID = self.getProperty(OB_PROP_FULLID)
        idLen = len(aFullID)
        aType = self.getProperty(OB_PROP_TYPE)
        if aType == OB_PROP_TYPE_SYSTEM:
            aFullID = str( aFullID )
        else:
            aFullID = aFullID.id
        maxShift = self.getMaxShiftPos(DIRECTION_RIGHT)
        newLabel = aFullID[0:oldLen]
        self.calcLabelParam(newLabel)
        totalWidth,limit = self.getLabelParam()
        while totalWidth<limit and oldLen <= len(aFullID):
            oldLen += 1
            newLabel = aFullID[0:oldLen]
            self.calcLabelParam(newLabel)
            totalWidth,limit = self.getLabelParam()
        if newLabel != aFullID:
            newLabel = newLabel[0:len(newLabel)-3]+'...'
        newDimx = self.estLabelWidth(newLabel)
        oldDimx = self.getProperty(OB_PROP_DIMENSION_X)
        deltaWidth = newDimx-oldDimx
        resizeCommand = lcmds.ResizeObject(self.getLayout(),self.getID(), 0, 0, 0, deltaWidth)            
        relabelCommand = lcmds.SetObjectProperty( self.getLayout(), self.getID(), OB_PROP_LABEL, newLabel )
        self.getLayout().passCommand( [resizeCommand,relabelCommand] )  

    def getMenuItems( self, aSubMenu = None ):
        menuDictList = ConcreteObject.getMenuItems( self, aSubMenu )
        menuDictList += {
            'extend label': self.__extend_label
            }
        return menuDictList

class SystemObject(EntityObject):
    def __init__( self, aLayout, objectID, parentObject, x, y, fullID ):
        EntityObject.__init__( self, aLayout, objectID, parentObject, x, y, fullID )
        self.theObjectMap = {}
        self.theSystemMap = {}
        self.properties [ OB_PROP_OUTLINE_WIDTH ] = 3
        self.properties[ OB_PROP_TYPE ] = OB_PROP_TYPE_SYSTEM
        self.properties [ OB_PROP_DIMENSION_X ] = SYS_MINWIDTH
        self.properties [ OB_PROP_DIMENSION_Y ] = SYS_MINHEIGHT
        self.properties [ OB_PROP_LABEL ] = str( fullID )
        self.properties [ OB_PROP_MIN_LABEL ] = SYS_MINLABEL
        self.theLabel = self.properties [ OB_PROP_LABEL ]

        self.theMaxShiftPosx = 0;self.theMaxShiftPosy = 0
        self.theMaxShiftNegx = 0;self.theMaxShiftNegy = 0
        self.theorgdir = 0
        self.accshiftx = 0;self.accshifty = 0
        self.prect1 = None;self.prect2 = None;self.rectdotx = 0;self.rectdoty = 0
        
        self.thex1org = 0
        self.they1org = 0
        self.thex2org = 0
        self.they2org = 0
        self.theduporg = 0
        self.theddownorg = 0
        self.thedleftorg = 0
        self.thedrightorg = 0
        
        aSystemSD = EntityObject.getShapeDescriptor(
            self, self.getProperty( OB_PROP_SHAPE_TYPE )
            )
        
        reqWidth = aSystemSD.getRequiredWidth()
        reqHeight = aSystemSD.getRequiredHeight()
        
        if isinstance( parentObject, Layout ):
            layoutDims = self.layout.getProperty( LO_SCROLL_REGION )
            self.properties [ OB_PROP_DIMENSION_X ] = layoutDims[2] - layoutDims[0]-1
            self.properties [ OB_PROP_DIMENSION_Y ] = layoutDims[3]- layoutDims[1]-1
        else:
            lblWidth = reqWidth
            x = self.getProperty(OB_PROP_POS_X)
            y = self.getProperty(OB_PROP_POS_Y)
            x2 = x+self.getProperty(OB_PROP_DIMENSION_X)
            y2 = y+self.getProperty(OB_PROP_DIMENSION_Y)
            px2 = self.parentObject.getProperty(SY_INSIDE_DIMENSION_X)
            py2 = self.parentObject.getProperty(SY_INSIDE_DIMENSION_Y)
            rpar = n.array([0,0,px2,py2])
            rn = self.createRnOut()
            availspace = self.parentObject.getAvailSpace(x,y,x2,y2,rn)
            #checkLabel
            if lblWidth>SYS_MINWIDTH:
                newLabel = self.truncateLabel(self.theLabel,lblWidth,SYS_MINWIDTH)
                self.properties [OB_PROP_LABEL] = newLabel
                aSystemSD.renameLabel (newLabel)
                
            lblWidth = aSystemSD.getRequiredWidth()
            
            largest = max(availspace/2,lblWidth)
            self.properties [ OB_PROP_DIMENSION_X ] = largest
            if largest ==availspace/2:
                diff = self.getProperty(OB_PROP_DIMENSION_X)-(x2-x)
                self.properties [ OB_PROP_DIMENSION_Y ] = y2-y+diff
        self.setShapeDescriptor( aSystemSD )

        self.properties[ SY_INSIDE_DIMENSION_X  ] = aSystemSD.getInsideWidth()
        self.properties[ SY_INSIDE_DIMENSION_Y  ] = aSystemSD.getInsideHeight()


        

        self.cursorMap = { DIRECTION_TOP_LEFT:CU_RESIZE_TOP_LEFT, DIRECTION_UP:CU_RESIZE_TOP, 
                 DIRECTION_TOP_RIGHT:CU_RESIZE_TOP_RIGHT, DIRECTION_RIGHT:CU_RESIZE_RIGHT,
                     DIRECTION_BOTTOM_RIGHT:CU_RESIZE_BOTTOM_RIGHT, DIRECTION_DOWN:CU_RESIZE_BOTTOM, 
                 DIRECTION_BOTTOM_LEFT:CU_RESIZE_BOTTOM_LEFT, DIRECTION_LEFT:CU_RESIZE_LEFT}

        self.dragMap = {DIRECTION_LEFT:n.array([[1,0],[0,0],[0,0],[0,0]]), 
                 DIRECTION_RIGHT:n.array([[0,0],[0,0],[1,0],[0,0]]),
                 DIRECTION_UP:n.array([[0,0],[0,1],[0,0],[0,0]]), 
                 DIRECTION_DOWN:n.array([[0,0],[0,0],[0,0],[0,1]]),
                 DIRECTION_BOTTOM_RIGHT:n.array([[0,0],[0,0],[1,0],[0,1]]), 
                 DIRECTION_BOTTOM_LEFT:n.array([[-1,0],[0,0],[0,0],[0,1]]),
                 DIRECTION_TOP_RIGHT:n.array([[0,0],[0,-1],[1,0],[0,0]]), 
                 DIRECTION_TOP_LEFT:n.array([[-1,0],[0,-1],[0,0],[0,0]])}


        #self.UDLRMap ={'U':0,'D':1,'L':2,'R':3}
        self.UDLRMap ={'L':0,'U':1,'R':2,'D':3}

    def getDMType():
        return SYSTEM

    def getSystemAtXY( self, x, y ):
        (x0, y0) = self.getAbsolutePosition()
        (x1,y1) = self.properties[ OB_PROP_DIMENSION_X] + x0, self.properties[OB_PROP_DIMENSION_Y] + y0 
        if x <x0 or x >x1 or y<y0 or y>y1:
            return None
        for aSubSystem in self.theSystemMap.values():
            retVal =  aSubSystem.getSystemAtXY( x, y )
            if retVal != None:
                return retVal
        return self
                
    def dispose( self ):
        for anObjectID in self.theObjectMap.keys()[:]:
            self.layout.deleteObject( anObjectID )
        EntityObject.dispose( self )

    def move( self, dx, dy ):
        EntityObject.move( self, dx,dy )
        for anObjectID in self.theObjectMap.keys():
            self.theObjectMap[ anObjectID ].parentMoved( dx, dy )

    def registerObject( self, anObject ):
        self.theObjectMap[anObject.getID()] = anObject
        if isinstance( anObject, SystemObject ):
            self.theSystemMap[anObject.getID()] = anObject

    def unregisterObject ( self, anObjectID ):
        anObject = self.theObjectMap[ anObjectID ]
        del self.theObjectMap[ anObjectID ]
        if isinstance( anObject, SystemObject ):
            del self.theSystemMap[ anObjectID ]
        
    def parentMoved( self, dx, dy ):
        EntityObject.parentMoved( self, dx, dy )
        for anID in self.theObjectMap.keys():
            self.layout.getObject( anID ).parentMoved( dx, dy )

    def pasteObject(self):
        (offsetx, offsety ) = self.getAbsolutePosition()
        x = self.newObjectPosX - (self.theSD.insideX + offsetx )
        y = self.newObjectPosY - ( self.theSD.insideY + offsety )
        aBuffer = self.getModelEditor().getCopyBuffer()
        #aType = aBuffer.getProperty(OB_PROP_TYPE)
        x2 = x+aBuffer.getProperty(OB_PROP_DIMENSION_X)
        y2 = y+aBuffer.getProperty(OB_PROP_DIMENSION_Y)
        px2 = self.getProperty(SY_INSIDE_DIMENSION_X)
        py2 = self.getProperty(SY_INSIDE_DIMENSION_Y)
        rpar = n.array([0,0,px2,py2])
        rn = self.createRnIn()
        availspace = self.getAvailSpace(x,y,x2,y2,rn)
        if availspace>0:
            if (not self.isOverlap(x,y,x2,y2,rn) and self.isWithinParent(x,y,x2,y2,rpar)):
                aCommand = lcmds.PasteObject( self.layout, aBuffer,x,y, self.id )
                self.layout.passCommand( [aCommand] )
            else:
                # change cursor
                self.theShape.setCursor(CU_CROSS)
        else:
            self.theShape.setCursor(CU_CROSS)       

    def canPaste(self):
        aBuffer = self.getModelEditor().getCopyBuffer()
        aType = aBuffer.getType()
        aParentFullID = self.getProperty(OB_PROP_FULLID)
        aSystemPath = aParentFullID.toSystemPath()
        if aType == 'SystemObjectBuffer':
            self.setExistObjectFullIDList()
            return self.canPasteOneSystemBuffer( aBuffer, aSystemPath )
        elif aType == "MultiObjectBuffer":
            self.setExistObjectFullIDList()
            for aSystemBufferName in aBuffer.getSystemObjectListBuffer().getObjectBufferList():
                aSystemBuffer = aBuffer.getSystemObjectListBuffer().getObjectBuffer( aSystemBufferName )
                if not self.canPasteOneSystemBuffer( aSystemBuffer, aSystemPath ):
                    return False
            return True
        else:
            return True

    def canPasteOneSystemBuffer( self, aBuffer, aSystemPath ):
        anObjName = aBuffer.getProperty( OB_PROP_FULLID ).id
        aFullID = identifiersFullID( SYSTEM, aSystemPath, anObjName )
        if not self.theModelEditor.getModel().isEntityExist( aFullID):
            return True
        else:
            return False
        
    def resize( self ,  deltaup, deltadown, deltaleft, deltaright  ):
        #first do a resize then a move
        # FIXME! IF ROOTSYSTEM RESIZES LAYOUT MUST BE RESIZED, TOOO!!!!
        # resize must be sum of deltas
        self.properties[ OB_PROP_DIMENSION_X ] += deltaleft + deltaright
        self.properties[ OB_PROP_DIMENSION_Y ] += deltaup + deltadown 
        self.properties[ SY_INSIDE_DIMENSION_X ] += deltaleft + deltaright
        self.properties[ SY_INSIDE_DIMENSION_Y ] += deltaup + deltadown 
        if self.theShape!= None:
            self.theShape.resize( deltaleft + deltaright, deltaup + deltadown )
        if deltaleft!= 0 or deltaup  != 0:
            self.move( -deltaleft, -deltaup )
        
    def setProperty(self, aPropertyName, aPropertyValue):
        EntityObject.setProperty(self, aPropertyName, aPropertyValue)
        if  self.theCanvas  != None:
            if aPropertyName == OB_PROP_DIMENSION_X :
                oldx = self.properties[ OB_PROP_DIMENSION_X ]
                deltaright = aPropertyValue - oldx
                self.resize( 0,0,0,deltaright )
                return
            if aPropertyName == OB_PROP_DIMENSION_Y :
                oldy = self.properties[ OB_PROP_DIMENSION_Y ]
                deltadown = aPropertyValue - oldy
                self.resize( 0,deltadown,0,0 )
                return
            
    def estLabelWidth(self,newLabel):
        height,width = self.getGraphUtils().getTextDimensions(newLabel)
        return width+16

    def labelChanged( self,aPropertyValue ):
        newLabel = aPropertyValue
        #totalWidth,limit = self.getLabelParam()
        #if totalWidth>limit:
        #   newLabel = self.truncateLabel(newLabel,totalWidth,limit)
        #   self.properties[OB_PROP_LABEL] = newLabel
        
        self.theShape.labelChanged(self.getProperty(OB_PROP_LABEL)) 
        
    def getEmptyPosition( self ):
        return ( 50,50 )

    def addItem( self, absx,absy ):
        buttonPressed = self.layout.getPaletteButton()
        if buttonPressed == PE_TEXT:
            pass
        elif buttonPressed == PE_SELECTOR:
            self.doSelect()
        elif buttonPressed == PE_CUSTOM:
            pass

        else:
            aCommand = self.createObject( absx, absy, buttonPressed )[0]

            if aCommand != None:
                self.layout.passCommand( [aCommand] )
            else:
                self.theShape.setCursor(CU_CROSS)
    
    def createObject( self, absx, absy, aType ):
        buttonPressed = aType        
        (offsetx, offsety ) = self.getAbsolutePosition()
        x = absx - (self.theSD.insideX + offsetx )
        y = absy - ( self.theSD.insideY + offsety )
        x2 = x
        y2 = y
        aSysPath = self.getProperty( OB_PROP_FULLID ).toSystemPath()
        aCommand = None
        px2 = self.getProperty(SY_INSIDE_DIMENSION_X)
        py2 = self.getProperty(SY_INSIDE_DIMENSION_Y)
        rpar = n.array([0,0,px2,py2])

        if buttonPressed == PE_SYSTEM:
            # create command
            aName = self.getModelEditor().getUniqueEntityName(
                SYSTEM, aSysPath )
            aFullID = identifiers.FullID( SYSTEM, aSysPath, aName )
            objectID = self.layout.getUniqueObjectID( OB_PROP_TYPE_SYSTEM )

            # check boundaries
            rn = self.createRnAddSystem()
            minreqx, minreqy = self.getMinDims( OB_PROP_TYPE_SYSTEM, aFullID )
            x2 = x + max( SYS_MINWIDTH, minreqx )
            y2 = y + max( SYS_MINHEIGHT, minreqy )

            availspace = self.getAvailSpace(x,y,x2,y2,rn)
            if availspace>0:
                if ( not self.isOverlap(x,y,x2,y2,rn ) and \
                   self.isWithinParent(x,y,x2,y2,rpar)):
                    aCommand = lcmds.CreateObject( self.layout, objectID, OB_PROP_TYPE_SYSTEM, aFullID, x, y, self )
        elif buttonPressed == PE_PROCESS:
            # create command
            aName = self.getModelEditor().getUniqueEntityName ( PROCESS, aSysPath )
            aFullID = identifiers.FullID( PROCESS, aSysPath, aName )
            objectID = self.layout.getUniqueObjectID( OB_PROP_TYPE_PROCESS )
            minreqx, minreqy = self.getMinDims( OB_PROP_TYPE_PROCESS, aFullID.id )
            x2 = x+max( PRO_MINWIDTH, minreqx )
            y2 = y+max( PRO_MINHEIGHT, minreqy )
            # check boundaries
            rn = self.createRnAddOthers()
            if (not self.isOverlap(x,y,x2,y2,rn) and \
               self.isWithinParent(x,y,x2,y2,rpar)):
                aCommand = lcmds.CreateObject( self.layout, objectID, OB_PROP_TYPE_PROCESS, aFullID, x, y, self )
        elif buttonPressed == PE_VARIABLE:
            # create command
            aName = self.getModelEditor().getUniqueEntityName(
                VARIABLE, aSysPath )
            aFullID = identifiers.FullID( VARIABLE, aSysPath, aName )
            objectID = self.layout.getUniqueObjectID( OB_PROP_TYPE_VARIABLE )
            
            minreqx, minreqy = self.getMinDims( OB_PROP_TYPE_VARIABLE, aFullID.id )
            x2 = x+max( VAR_MINWIDTH, minreqx )
            y2 = y+max( VAR_MINHEIGHT, minreqy )
            # check boundaries
            rn = self.createRnAddOthers()
            if (not self.isOverlap(x,y,x2,y2,rn) and self.isWithinParent(x,y,x2,y2,rpar)):
                aCommand = lcmds.CreateObject( self.layout, objectID, OB_PROP_TYPE_VARIABLE, aFullID, x, y, self )
        return aCommand, x2-x, y2-y

    def getObjectList( self ):
        # return IDs
        return self.theObjectMap.keys()

    def getObject( self, anObjectID ):
        return self.theObjectMap[ anObjectID ]
        
    def isWithinSystem( self, objectID ):
        #returns true if is within system
        pass
        
    def getAbsoluteInsidePosition( self ):
        ( x, y ) = self.getAbsolutePosition()
        return ( x+ self.theSD.insideX, y+self.theSD.insideY )
    
    def getCursorType( self, aFunction, x, y, buttonPressed ):
        maxposx = 0;maxposy = 0;maxnegx = 0;maxnegy = 0;maxpos = 0;maxneg = 0
        oneDirList = [DIRECTION_RIGHT,DIRECTION_UP,DIRECTION_DOWN,DIRECTION_LEFT]
        try:
            aCursorType = EntityObject.getCursorType( self, aFunction, x, y, buttonPressed )
            if aFunction == SD_SYSTEM_CANVAS and self.layout.getPaletteButton() != PE_SELECTOR:
                aCursorType = CU_ADD
            elif aFunction == SD_OUTLINE:
                olw = self.getProperty( OB_PROP_OUTLINE_WIDTH )
                direction = self.getDirection( x, y )
                if isinstance( self.parentObject, l.Layout ):
                    return self.cursorMap[direction]
                if direction in oneDirList:
                    maxpos = self.getMaxShiftPos(direction)
                    maxneg = self.getMaxShiftNeg(direction)
                    if maxpos>0 or maxneg>0 :
                        aCursorType = self.cursorMap[direction]
                    else:
                        aCursorType = CU_CROSS
                else:
                    maxposx,maxposy = self.getMaxShiftPos(direction)
                    maxnegx,maxnegy = self.getMaxShiftNeg(direction)
                    if maxposx>0 or maxposy>0 or maxnegx>0 or maxnegy>0  :
                        aCursorType = self.cursorMap[direction]
                    else:
                        aCursorType = CU_CROSS

                
        except:
            pass
        return aCursorType

    def getDirection( self, absx, absy ):
        olw = self.getProperty( OB_PROP_OUTLINE_WIDTH )
        width = self.getProperty( OB_PROP_DIMENSION_X )
        height = self.getProperty( OB_PROP_DIMENSION_Y )
        (offsetx, offsety ) = self.getAbsolutePosition()
        x = absx- offsetx
        y = absy - offsety

        direction = 0
        #leftwise direction:
        if x <= olw:
            direction |= DIRECTION_LEFT
        
        # rightwise direction
        elif x>= width -olw:
            direction |= DIRECTION_RIGHT

        # upwards direction
        if y <= olw:
            direction |= DIRECTION_UP
            

        # downwards direction
        elif y>= height - olw:
            direction |= DIRECTION_DOWN
            
            
        return direction

    def outlineDragged( self, dx, dy, absx, absy):
        theParent = self.parentObject
        direction = self.getDirection( absx, absy )
        
        if not self.theShape.getIsButtonPressed() : # button released
            self.thedleftorg = self.properties[OB_PROP_POS_X]-self.thex1org
            self.thedrightorg = self.properties[OB_PROP_POS_X]+self.properties[OB_PROP_DIMENSION_X]-self.thex2org
            self.theduporg = self.properties[OB_PROP_POS_Y]-self.they1org
            self.theddownorg = self.properties[OB_PROP_POS_Y]+self.properties[OB_PROP_DIMENSION_Y]-self.they2org
            self.resize( self.theduporg, -self.theddownorg, self.thedleftorg, -self.thedrightorg)
            aCommand = lcmds.ResizeObject( self.layout, self.id, -self.theduporg, self.theddownorg, -self.thedleftorg, self.thedrightorg )

            # Layout
            newScrollRegion = self.layout.getProperty(LO_SCROLL_REGION)
            self.layout.setProperty(LO_SCROLL_REGION,self.layout.orgScrollRegion)
            self.layout.setProperty(OB_PROP_DIMENSION_X,self.layout.orgScrollRegion[2]-self.layout.orgScrollRegion[0])
            self.layout.setProperty(OB_PROP_DIMENSION_Y,self.layout.orgScrollRegion[3]-self.layout.orgScrollRegion[1])
            self.layout.getCanvas().setSize(self.layout.orgScrollRegion)
            aCommandLayout = lcmds.ChangeLayoutProperty(self.layout, LO_SCROLL_REGION,newScrollRegion)
            self.layout.passCommand( [aCommand,aCommandLayout] )
            
        
        
        #FIXMEparentObject boundaries should be watched!!!
        if self.theShape.getFirstDrag() and not self.theShape.getDragBefore() :
            self.thex1org = self.properties[OB_PROP_POS_X]
            self.they1org = self.properties[OB_PROP_POS_Y]
            self.thex2org = self.thex1org+self.properties[OB_PROP_DIMENSION_X]
            self.they2org = self.they1org+self.properties[OB_PROP_DIMENSION_Y]
            if isinstance( theParent, l.Layout ):
                if direction ==DIRECTION_UP or direction ==DIRECTION_DOWN:
                    self.theMaxShiftPosy = self.getMaxShiftPos(direction)
                elif direction ==DIRECTION_RIGHT or direction ==DIRECTION_LEFT:
                    self.theMaxShiftPosx = self.getMaxShiftPos(direction)
                else:
                    self.theMaxShiftPosx,self.theMaxShiftPosy = self.getMaxShiftPos(direction)
            if direction ==DIRECTION_UP or direction ==DIRECTION_DOWN:
                self.theMaxShiftNegy = -(self.getMaxShiftNeg(direction))
            elif direction ==DIRECTION_RIGHT or direction ==DIRECTION_LEFT:
                self.theMaxShiftNegx = -(self.getMaxShiftNeg(direction))
            else:
                self.theMaxShiftNegx,self.theMaxShiftNegy = (self.getMaxShiftNeg(direction))
                self.theMaxShiftNegx = -self.theMaxShiftNegx
                self.theMaxShiftNegy = -self.theMaxShiftNegy
                
            lblWidth = self.theSD.getRequiredWidth()
            dimx = self.properties[ OB_PROP_DIMENSION_X ]
            limitX = -(dimx-lblWidth)
            if limitX<0 and self.theMaxShiftNegx<limitX:
                self.theMaxShiftNegx = limitX

            self.theorgdir = direction
            self.layout.orgScrollRegion = self.layout.getProperty(LO_SCROLL_REGION)
            self.accshiftx = 0;self.accshifty = 0

            if direction not in [DIRECTION_RIGHT,DIRECTION_UP,DIRECTION_DOWN,DIRECTION_LEFT]:
                twoRectMat = self.getGraphUtils().buildTwoRect(self.thex1org,self.they1org,self.thex2org,self.they2org,self.theMaxShiftPosx,self.theMaxShiftPosy,self.theMaxShiftNegx,self.theMaxShiftNegy,self.theorgdir)
                self.prect1 = n.array([twoRectMat[0][0],twoRectMat[0][1],twoRectMat[0][2],twoRectMat[0][3]])
                self.prect2 = n.array([twoRectMat[1][0],twoRectMat[1][1],twoRectMat[1][2],twoRectMat[1][3]])
                self.rectdotx,self.rectdoty = self.getGraphUtils().getRectDotxy(self.thex1org,self.they1org,self.thex2org,self.they2org,self.theorgdir)
            
            
            self.theShape.setFirstDrag(False)
            self.theShape.setDragBefore(True)
            

        UDLR = self.getUDLRmatrix(dx,dy,self.theorgdir)
        deltaup = UDLR[self.UDLRMap['U']]
        deltadown = UDLR[self.UDLRMap['D']]
        deltaright = UDLR[self.UDLRMap['R']]
        deltaleft = UDLR[self.UDLRMap['L']]
        
        if direction != self.theorgdir:
            direction = self.theorgdir
        
        
        if self.theShape.getIsButtonPressed() and self.theorgdir ==direction:
            if direction in [DIRECTION_RIGHT,DIRECTION_UP,DIRECTION_DOWN,DIRECTION_LEFT]:
                if direction ==DIRECTION_UP or direction ==DIRECTION_DOWN:
                    if direction ==DIRECTION_UP:
                        dy = -dy
                    newAccShift = self.accshifty+dy
                    if newAccShift>0 and newAccShift<self.theMaxShiftPosy:
                        self.accshifty += dy
                        self.resize( deltaup, deltadown, deltaleft, deltaright)
                        if isinstance( theParent, l.Layout ):
                            self.adjustLayoutCanvas(   deltaup, deltadown, deltaleft, deltaright )
                        else:
                            self.adjustCanvas(dx,dy)
                    elif newAccShift<0 and newAccShift>self.theMaxShiftNegy:
                        self.accshifty += dy
                        self.resize( deltaup, deltadown, deltaleft, deltaright)
                        if isinstance( theParent, l.Layout ):
                            self.adjustLayoutCanvas(   deltaup, deltadown, deltaleft, deltaright )
                        else:
                            self.adjustCanvas(dx,dy)

                if direction ==DIRECTION_LEFT or direction ==DIRECTION_RIGHT:
                    if direction ==DIRECTION_LEFT:
                        dx = -dx
                    newAccShift = self.accshiftx+dx   
                    if newAccShift>0 and newAccShift<self.theMaxShiftPosx:
                        self.accshiftx += dx
                        self.resize( deltaup, deltadown, deltaleft, deltaright)
                        if isinstance( theParent, l.Layout ):
                            self.adjustLayoutCanvas(   deltaup, deltadown, deltaleft, deltaright )
                        else:
                            self.adjustCanvas(dx,dy)
                    elif newAccShift<0 and newAccShift>self.theMaxShiftNegx:
                        self.accshiftx += dx
                        self.resize( deltaup, deltadown, deltaleft, deltaright)
                        if isinstance( theParent, l.Layout ):
                            self.adjustLayoutCanvas(   deltaup, deltadown, deltaleft, deltaright )
                        else:
                            self.adjustCanvas(dx,dy)
            else:
                newdotx = self.rectdotx+dx
                newdoty = self.rectdoty+dy
                cond1 = self.isWithinParent(newdotx,newdoty,newdotx,newdoty,self.prect1)
                cond2 = self.isWithinParent(newdotx,newdoty,newdotx,newdoty,self.prect2)
                if cond1 and cond2:
                    self.rectdotx = newdotx
                    self.rectdoty = newdoty
                    self.resize( deltaup, deltadown, deltaleft, deltaright)
                    if isinstance( theParent, l.Layout ):
                        self.adjustLayoutCanvas(   deltaup, deltadown, deltaleft, deltaright )
                    else:
                        self.adjustCanvas(dx,dy)
                else:
                    return
            
    def getAvailableSystemShape(self):
            return self.theSystemShapeList

    def getLargestChildPosXY(self):
        childMaxX = 0
        childMaxY = 0
        childs = self.getObjectList()
        for ch in childs:
            achild = self.getObject(ch)
            chx = achild.getProperty(OB_PROP_POS_X)+achild.getProperty(OB_PROP_DIMENSION_X)
            chy = achild.getProperty(OB_PROP_POS_Y)+achild.getProperty(OB_PROP_DIMENSION_Y)
            childMaxX = max( childMaxX, chx )
            childMaxY = max( childMaxY, chy )
        return childMaxX, childMaxY
        
    def createRnOut(self):
        no = len(self.parentObject.getObjectList())
        rn = None
        if no>1:
            for sib in self.parentObject.getObjectList():
                asib = self.parentObject.getObject(sib)
                if asib.getProperty(OB_PROP_TYPE) != OB_PROP_TYPE_CONNECTION and asib.getProperty(OB_PROP_FULLID) != self.getProperty(OB_PROP_FULLID):
                    asibx1 = asib.getProperty(OB_PROP_POS_X)
                    asiby1 = asib.getProperty(OB_PROP_POS_Y)
                    asibx2 = asibx1+asib.getProperty(OB_PROP_DIMENSION_X)
                    asiby2 = asiby1+asib.getProperty(OB_PROP_DIMENSION_Y)
                    rsib = n.array([asibx1,asiby1,asibx2,asiby2])
                    rsib = n.reshape(rsib,(4,1))
                    if rn ==None:
                        rn = rsib
                    else:
                        rn = n.concatenate((rn,rsib),1)
        return rn
    
    def createRnIn(self):
        no = len(self.getObjectList())
        rn = None
        olw = self.getProperty(OB_PROP_OUTLINE_WIDTH)
        if no>0:
            for ch in self.getObjectList():
                ach = self.getObject(ch)
                achx1 = ach.getProperty(OB_PROP_POS_X)
                achy1 = ach.getProperty(OB_PROP_POS_Y)
                achx2 = achx1+ach.getProperty(OB_PROP_DIMENSION_X)
                achy2 = achy1+ach.getProperty(OB_PROP_DIMENSION_Y)+8*olw
                rch = n.array([achx1,achy1,achx2,achy2])
                rch = n.reshape(rch,(4,1))
                if rn ==None:
                    rn = rch
                else:
                    rn = n.concatenate((rn,rch),1)
        return rn

    def createRnAddSystem(self):
        no = len(self.getObjectList())
        rn = None
        if no>0:
            for sib in self.getObjectList():
                asib = self.getObject(sib)
                asibx1 = asib.getProperty(OB_PROP_POS_X)
                asiby1 = asib.getProperty(OB_PROP_POS_Y)
                asibx2 = asibx1+asib.getProperty(OB_PROP_DIMENSION_X)
                asiby2 = asiby1+asib.getProperty(OB_PROP_DIMENSION_Y)
                rsib = n.array([asibx1,asiby1,asibx2,asiby2])
                rsib = n.reshape(rsib,(4,1))
                if rn ==None:
                    rn = rsib
                else:
                    rn = n.concatenate((rn,rsib),1)
        return rn

    def createRnAddOthers(self):
        no = len(self.getObjectList())
        rn = None
        if no>0:
            for sib in self.getObjectList():
                asib = self.getObject(sib)
                if asib.getProperty(OB_PROP_TYPE) ==OB_PROP_TYPE_SYSTEM:
                    asibx1 = asib.getProperty(OB_PROP_POS_X)
                    asiby1 = asib.getProperty(OB_PROP_POS_Y)
                    asibx2 = asibx1+asib.getProperty(OB_PROP_DIMENSION_X)
                    asiby2 = asiby1+asib.getProperty(OB_PROP_DIMENSION_Y)
                    rsib = n.array([asibx1,asiby1,asibx2,asiby2])
                    rsib = n.reshape(rsib,(4,1))
                    if rn ==None:
                        rn = rsib
                    else:
                        rn = n.concatenate((rn,rsib),1)
        return rn

    def getMaxShiftNeg(self,direction):
        """a system is being resized inwardly"""
        dir = direction
        x1 = self.getProperty(OB_PROP_POS_X)
        y1 = self.getProperty(OB_PROP_POS_Y)
        #x1 = 0;y1 = 0
        x2 = x1+self.getProperty(OB_PROP_DIMENSION_X)
        y2 = y1+self.getProperty(OB_PROP_DIMENSION_Y)
        r1 = n.array([x1,y1,x2,y2])
        rn = self.createRnIn()
        textWidth = self.properties[ OB_PROP_SHAPE_DESCRIPTOR_LIST ].getRequiredWidth()
        textHeight = self.properties[ OB_PROP_SHAPE_DESCRIPTOR_LIST ].getRequiredHeight()
        if rn ==None:
            olw = self.properties[ OB_PROP_OUTLINE_WIDTH ] 
            u1 = x1+(self.getProperty(OB_PROP_DIMENSION_X)-textWidth)
            v1 = y1+(y2-y1-textHeight)
            u2 = x2-(self.getProperty(OB_PROP_DIMENSION_X)-textWidth)
            v2 = y2-(y2-y1-textHeight)
            matrix = n.array([u1,v1,u2,v2])
        else:
            matrix = self.getGraphUtils().calcMaxShiftNeg(r1,rn,dir)
        mshift = matrix-r1
        if len(self.maxShiftMap[dir])>1:
            posx,posy = self.maxShiftMap[dir][0],self.maxShiftMap[dir][1]
            return abs( mshift[posx] ),abs( mshift[posy] )
        else:
            pos = self.maxShiftMap[dir][0]
            return abs( mshift[pos] )
        
    def getUDLRmatrix(self,dx,dy,dir):
        """Up Down Left Right Matrix"""
        m = n.array([dx,dy])
        m = n.reshape(m,(2,1))
        m = n.dot(self.dragMap[dir],m)
        m = n.reshape(m,(4,))
        if dir ==DIRECTION_LEFT:
            m[self.UDLRMap['L']] = -m[self.UDLRMap['L']]
        if dir ==DIRECTION_UP:
            m[self.UDLRMap['U']] = -m[self.UDLRMap['U']]
        return m

    def getDelta(self,UDLRmatrix):
        m = UDLRmatrix
        pos = n.nonzero(m)
        delta = 0
        if n.size(pos) ==1:
            delta = m[pos[0]]
            return delta
        if n.size(pos) ==0:
            return delta
        mat = n.array([m[pos[0]],m[pos[1]]])
        if self.getGraphUtils().allGreater(mat):
            return max(m[pos[0]],m[pos[1]])
        elif self.getGraphUtils().allSmaller(mat):  
            return min(m[pos[0]],m[pos[1]])
        else:
            return max(abs(m[pos[0]]),abs(m[pos[1]]))
        
    def getAvailSpace(self,x,y,x2,y2,rn):
        px = 0
        py = 0
        px2 = self.getProperty(OB_PROP_DIMENSION_X)
        py2 = self.getProperty(OB_PROP_DIMENSION_Y)
        rpar = n.array([px,py,px2,py2])
        r1 = n.array([x,y,x2,y2])
        dir = DIRECTION_BOTTOM_RIGHT
        matrix = self.getGraphUtils().calcMaxShiftPos(r1,rn,dir,rpar)
        mspace = matrix-r1
        mshift = n.array( [-1,-1,1,1] )
        mspace = mspace * mshift
        if len(self.maxShiftMap[dir]) ==1:
            listpos = self.maxShiftMap[dir]
            pos = listpos[0]
            return max(0,mspace[pos])
        else:
            listpos = self.maxShiftMap[dir]
            posa = listpos[0]
            posb = listpos[1]
            spacea = max(0,mspace[posa])
            spaceb = max(0,mspace[posb])
            return max(spacea,spaceb)

    def getSystemObject(self):
        return self

    def getMenuItems( self, aSubMenu = None ):
        menuDictList = EntityObject.getMenuItems( self, aSubMenu )
        menuDictList += {
            'show system': lambda menu: None,
            'show process': lambda menu: None,
            'show variable': lambda menu: None
            }
        return menuDictList

class ProcessObject( EntityObject ):
    def __init__( self, aLayout, objectID, parentObject, x, y, fullID ):
        EntityObject.__init__( self, aLayout, objectID, parentObject, x, y, fullID )
        self.properties [ OB_PROP_FILL_COLOR ] = self.layout.graphUtils().getRRGByName("grey")

        self.properties [ OB_PROP_OUTLINE_WIDTH ] = 3
        self.properties[ OB_PROP_TYPE ] = OB_PROP_TYPE_PROCESS
        self.properties[ PR_CONNECTIONLIST ] = []
        #default dimensions
        self.properties [ OB_PROP_LABEL ] = fullID.id
        self.theLabel = self.properties [ OB_PROP_LABEL ]
        self.properties [ OB_PROP_MIN_LABEL ] = PRO_MINLABEL
        aProcessSD = EntityObject.getShapeDescriptor(self, self.getProperty( OB_PROP_SHAPE_TYPE ) )
        # first get text width and heigth

        reqWidth = aProcessSD.getRequiredWidth()
        reqHeight = aProcessSD.getRequiredHeight()
        
    
        self.properties [ OB_PROP_DIMENSION_X ] = reqWidth
        if reqWidth<PRO_MINWIDTH:
            self.properties [ OB_PROP_DIMENSION_X ] = PRO_MINWIDTH
        
        self.properties [ OB_PROP_DIMENSION_Y ] = reqHeight
        if reqHeight<PRO_MINHEIGHT:
            self.properties [ OB_PROP_DIMENSION_Y ] = PRO_MINHEIGHT

        self.connectionDragged = False
        aProcessSD.reCalculate()
        self.setShapeDescriptor( aProcessSD )

    def getDMType():
        return PROCESS

    def registerConnection( self, aConnectionID ):
        self.properties[ PR_CONNECTIONLIST ].append( aConnectionID )

    def unRegisterConnection( self, aConnectionID ):
        self.properties[PR_CONNECTIONLIST].remove( aConnectionID )

    def getAvailableProcessShape(self):
        return self.theProcessShapeList

    def dispose( self ):
        connList = self.properties[ PR_CONNECTIONLIST ][:]
        for aConnID in connList:
            self.layout.deleteObject( aConnID )
        EntityObject.dispose( self )

    def parentMoved( self, dx, dy ):
        EntityObject.parentMoved( self, dx, dy )

        for aConID in self.properties[PR_CONNECTIONLIST]:
            self.layout.getObject( aConID ).parentMoved( self.id, dx, dy )

    def move( self, dx, dy ):
        EntityObject.move( self, dx,dy)
        for aConID in self.properties[PR_CONNECTIONLIST]:
            self.layout.getObject( aConID ).parentMoved( self.id, dx, dy )

    def resize( self ,  deltaup, deltadown, deltaleft, deltaright  ):
        #first do a resize then a move
        # FIXME! IF ROOTSYSTEM RESIZES LAYOUT MUST BE RESIZED, TOOO!!!!
        # resize must be sum of deltas 
        self.properties[ OB_PROP_DIMENSION_X ] += deltaleft + deltaright
        self.properties[ OB_PROP_DIMENSION_Y ] += deltaup + deltadown 
        self.theShape.resize(deltaleft + deltaright,deltaup + deltadown )

    def setShapeDescriptor( self, anSD ):
        EntityObject.setShapeDescriptor( self, anSD )
        for aConnectionID in self.properties[ PR_CONNECTIONLIST]:
            aConnectionObject = self.layout.getObject( aConnectionID )
            aConnectionObject.reconnect()

    def buttonReleased( self ):
        EntityObject.buttonReleased( self )
        if self.connectionDragged:
            self.connectionDragged = False
            # get coordinates
            ( endx, endy) = self.theGhostLine.getEndPoint( )
            self.theGhostLine.delete()
            self.theGhostLine = None
            # delete ghostline
            # CHECK IF VARIABLE IS CONNECTED
            ( variableID, variableRing ) = self.layout.checkConnection( endx, endy, DM_TYPE_VARIABLE )
            newVarrefName = None
            if variableID == None:
                aCommand , width, height = self.layout.thePackingStrategy.createEntity( DM_TYPE_VARIABLE, endx, endy )
                # create totally new variable
                if aCommand == None:
                    self.theShape.setCursor( CU_CROSS )
                    variableID = None
                else:
                    ringSource, ringDest = self.layout.thePackingStrategy.autoConnect( self.getID(), (endx+width/2, endy+height/2) )
                    newID = self.layout.getUniqueObjectID( OB_PROP_TYPE_CONNECTION )
                    newVarrefName = self.__getNewVarrefID ()

                    connectCommand = lcmds.CreateConnection( self.layout, newID, self.id, aCommand.getID(), self.theRingCode, ringDest, PROCESS_TO_VARIABLE, newVarrefName )
                    self.layout.passCommand( [ aCommand] )
                    self.layout.passCommand( [ connectCommand ] )
                    variableID = aCommand.getID()
            # create real line
            else:
                # check for already existing varref
                varObject = self.layout.getObject(variableID)
                variableFullID = varObject.getProperty(OB_PROP_FULLID)
                relFullID = ecell.util.getRelativeReference(self.getProperty(OB_PROP_FULLID), variableFullID)
                #get the process varreflist
                aProFullPN = identifiers.FullPN(
                    self.getProperty(OB_PROP_FULLID), DMINFO_PROCESS_VARREFLIST )
                aVarrefList = ecell.util.copyValue( self.getModelEditor().getModel().getEntityProperty( aProFullPN) )
                #filter aVarrefList by variableFullID
                aSpecVarrefList = []
                for aVarref in aVarrefList:
                    if aVarref[ME_VARREF_FULLID] in (variableFullID,relFullID):
                        aSpecVarrefList += [aVarref]
                #get the pro connection obj  
                connectionList = self.getProperty(PR_CONNECTIONLIST)
                displayedVarrefList = []
                aSpecDisplayedVarrefList = []
                for conn in connectionList:
                    connObj = self.layout.getObject( conn )
                    varreffName = connObj.getProperty(CO_NAME)
                    varID = connObj.getProperty(CO_VARIABLE_ATTACHED)
                    #get var FUllID
                    if varID != None:
                        varFullID = self.layout.getObject( varID ).getProperty(OB_PROP_FULLID)
                        displayedVarrefList += [ [ varreffName, varFullID ] ]
                for aVarref in displayedVarrefList:
                    if aVarref[ME_VARREF_FULLID] == variableFullID:
                        aSpecDisplayedVarrefList += [ aVarref [ ME_VARREF_NAME ] ]
                
                
                #check if there is existing varref that hasn't been displayed
                if len(aSpecVarrefList) != len(aSpecDisplayedVarrefList) :
                    for aVarref in aSpecVarrefList:
                        if aVarref[ME_VARREF_NAME] not in aSpecDisplayedVarrefList:
                            newVarrefName = aVarref[ME_VARREF_NAME]
            
            
                newID = self.layout.getUniqueObjectID( OB_PROP_TYPE_CONNECTION )
                if newVarrefName == None:
                    newVarrefName = self.__getNewVarrefID ()
                aCommand = lcmds.CreateConnection( self.layout, newID, self.id, variableID, self.theRingCode, variableRing, PROCESS_TO_VARIABLE, newVarrefName )
                self.layout.passCommand( [ aCommand ] )
            if variableID != None:
                self.layout.selectRequest( variableID )
            # newCon = self.layout.getObject( newID )
            # newCon.checkConnections()
            
    def ringDragged( self, aShapeName, dx, dy ):
        if self.connectionDragged:
            self.theGhostLine.moveEndPoint( dx, dy )
        else:
            self.theRingCode = aShapeName
            
            ( x, y ) = self.getRingPosition( aShapeName )
            x += self.theSD.getRingSize()/2
            y += self.theSD.getRingSize()/2
            self.theGhostLine = GhostLine( self, aShapeName, x+dx, y+dy )
            self.connectionDragged = True
        
    def getRingSize( self ):
        return self.theSD.getRingSize()

    def getRingPosition( self, ringCode ):
        #return absolute position of ring
        (xRing,yRing) = self.theSD.getShapeAbsolutePosition(ringCode)
        ( x, y ) = self.getAbsolutePosition()
        return (x+xRing, y+yRing )

    def estLabelWidth(self,newLabel):
        #height,width = self.getGraphUtils().getTextDimensions(newLabel)
        #return width+2+9
        return self.theSD.estLabelWidth(newLabel)

    def labelChanged( self,aPropertyValue ):
        newLabel = aPropertyValue
        self.theShape.labelChanged(self.getProperty(OB_PROP_LABEL)) 
        
        if self.properties[ PR_CONNECTIONLIST ]  != []:
                
            for conn in self.getProperty(PR_CONNECTIONLIST):
                conobj =  self.layout.getObject(conn)
                (x, y) = self.getRingPosition(conobj.properties[ CO_PROCESS_RING ] )
                rsize = self.getRingSize()
                # this shoould be done by connection object enpoint1chgd
                conobj.properties[ CO_ENDPOINT1 ] = [ x +rsize/2, y+rsize/2 ]
                conobj.properties[ OB_PROP_SHAPE_DESCRIPTOR_LIST ].reCalculate()
                conobj.theShape.repaint()

    def __getNewVarrefID( self ):
        aFullID = self.getProperty( OB_PROP_FULLID )
        aFullPN = identifiers.FullPN( aFullID, DMINFO_PROCESS_VARREFLIST )
        aVarrefList = self.layout.layoutManager.theModelEditor.getModel().getEntityProperty( aFullPN )
        aVarrefNameList = []
        for aVarref in aVarrefList:
            aVarrefNameList.append( aVarref[ME_VARREF_NAME] )
        i= 0
        while 'X' +str(i) in aVarrefNameList:
            i += 1
        return 'X' + str( i )

    def getCursorType( self, aFunction, x, y, buttonPressed ):
        cursorType = EntityObject.getCursorType( self,  aFunction, x, y, buttonPressed  )
        if aFunction == SD_RING and buttonPressed:
            return CU_CONN_INIT
        return cursorType 

    def getMenuItems( self, aSubMenu = None ):
        menuDictList = EntityObject.getMenuItems( self, aSubMenu )

        menuDictList += {
            'show connection': lambda menu: None
            }

        return menuDictList

class VariableObject( EntityObject ):
    def __init__( self, aLayout, objectID, parentObject, x, y, fullID ):
        EntityObject.__init__( self, aLayout, objectID, parentObject, x, y, fullID )
        self.theObjectMap = {}
        self.properties [ OB_PROP_OUTLINE_WIDTH ] = 3
        self.properties[ OB_PROP_TYPE ] = OB_PROP_TYPE_VARIABLE
        #default dimensions
        self.properties [ OB_PROP_LABEL ] = fullID.id
        self.properties [ OB_PROP_MIN_LABEL ] = VAR_MINLABEL
        aVariableSD = self.getShapeDescriptor(
            self.getProperty( OB_PROP_SHAPE_TYPE ) )
        # first get text width and heigth
        self.properties[ VR_CONNECTIONLIST ]= []
        reqWidth = aVariableSD.getRequiredWidth()
        reqHeight = aVariableSD.getRequiredHeight()
        self.connectionDragged = False

        self.properties [ OB_PROP_DIMENSION_X ] = reqWidth
        if reqWidth<VAR_MINWIDTH:
            self.properties [ OB_PROP_DIMENSION_X ] = VAR_MINWIDTH


        self.properties [ OB_PROP_DIMENSION_Y ] = reqHeight
        if reqHeight<VAR_MINHEIGHT:
            self.properties [ OB_PROP_DIMENSION_Y] = VAR_MINHEIGHT
        aVariableSD.reCalculate()
        self.setShapeDescriptor( aVariableSD )

    def getDMType():
        return VARIABLE

    def reconnect( self ):
        pass

    def dispose( self ):
        connList = self.properties[ VR_CONNECTIONLIST ][:]
        for aConnID in connList:
            self.layout.deleteObject( aConnID )
        EntityObject.dispose( self )

    def registerConnection( self, aConnectionID ):
        self.properties[ VR_CONNECTIONLIST ].append( aConnectionID )

    def unRegisterConnection( self, aConnectionID ):
        
        self.properties[ VR_CONNECTIONLIST].remove( aConnectionID )

    def setShapeDescriptor( self, anSD ):
        EntityObject.setShapeDescriptor( self, anSD )
        for aConnectionID in self.properties[ VR_CONNECTIONLIST]:
            aConnectionObject = self.layout.getObject( aConnectionID )
            aConnectionObject.reconnect()

    def estLabelWidth(self,newLabel):
        #height,width = self.getGraphUtils().getTextDimensions(newLabel)
        #return width+46
        return self.theSD.estLabelWidth(newLabel)

    def labelChanged( self,aPropertyValue ):
        newLabel = aPropertyValue
        self.theShape.labelChanged(self.getProperty(OB_PROP_LABEL))  

    def getAvailableVariableShape(self):
        return self.theVariableShapeList

    def parentMoved( self, dx, dy ):
        EntityObject.parentMoved( self, dx, dy )
        for aConID in self.properties[VR_CONNECTIONLIST]:
            self.layout.getObject( aConID ).parentMoved( self.id, dx, dy )

    def move( self, dx, dy ):
        EntityObject.move( self, dx,dy)
        for aConID in self.properties[VR_CONNECTIONLIST]:
            self.layout.getObject( aConID ).parentMoved( self.id, dx, dy )

    def registerObject( self, anObject ):
        self.theObjectMap[anObject.getID()] = anObject

    def unregisterObject ( self, anObjectID ):
        self.theObjectMap.__delitem__( anObjectID )

    def resize( self ,  deltaup, deltadown, deltaleft, deltaright  ):
        #first do a resize then a move
        # FIXME! IF ROOTSYSTEM RESIZES LAYOUT MUST BE RESIZED, TOOO!!!!
        # resize must be sum of deltas
        self.properties[ OB_PROP_DIMENSION_X ] += deltaleft + deltaright
        self.properties[ OB_PROP_DIMENSION_Y ] += deltaup + deltadown

        self.theShape.resize(deltaleft + deltaright,deltaup + deltadown)
        if self.properties[ VR_CONNECTIONLIST ]  != []:
                
            for conn in self.getProperty(VR_CONNECTIONLIST):
                conobj =  self.layout.getObject(conn)
                (x, y) = self.getRingPosition(conobj.properties[ CO_VARIABLE_RING ] )
                ringsize =  self.theSD.getRingSize()/2
                conobj.properties[ CO_ENDPOINT2 ] = [ x + ringsize, y+ringsize]
                conobj.properties[ OB_PROP_SHAPE_DESCRIPTOR_LIST ].reCalculate()
                conobj.theShape.repaint()

    def buttonReleased( self ):
        EntityObject.buttonReleased( self )
        if self.connectionDragged:
            self.connectionDragged = False
            # get coordinates
            ( endx, endy) = self.theGhostLine.getEndPoint( )
            self.theGhostLine.delete()
            self.theGhostLine = None
            # delete ghostline
            # CHECK IF VARIABLE IS CONNECTED
            ( processID, processRing ) = self.layout.checkConnection( endx, endy, DM_TYPE_PROCESS )
            newVarrefName = None
            if processID == None:
                cmdList = []
                # create a Process and a Variable
                ( varID, varRing ) = self.layout.checkConnection( endx, endy, DM_TYPE_VARIABLE )
                if varID == None:
                    varx, vary = endx, endy
                    varCommand , varwidth, varheight = self.layout.thePackingStrategy.createEntity( DM_TYPE_VARIABLE, varx, vary )
                    if varCommand == None:
                        self.theShape.setCursor( CU_CROSS )
                        return
                    varID = varCommand.getID()
                    cmdList.append( varCommand )
                else:
                    varObject = self.layout.getObject( varID )
                    varx, vary = varObject.getAbsolutePosition()
                    varwidth, varheight = varObject.getProperty( OB_PROP_DIMENSION_X), varObject.getProperty( OB_PROP_DIMENSION_Y )
                i = 0
                startx, starty = self.getAbsolutePosition()
                startx += self.getProperty(OB_PROP_DIMENSION_X)/2
                starty += self.getProperty( OB_PROP_DIMENSION_Y )/2
                varx += varwidth/2
                vary += varheight/2
                diffx, diffy = varx - startx, vary - starty
                procCommand = None
                while i != 5 and procCommand == None :
                    procx, procy = startx + (i + 5) * diffx/10, starty + (i + 5) *diffy/10
                    procCommand, procwidth, procheight = self.layout.thePackingStrategy.createEntity( DM_TYPE_PROCESS, procx, procy )
                    i *= -1
                    if i >= 0:
                        i  += 1
                if procCommand == None:
                    self.theShape.setCursor( CU_CROSS )
                    return
                procID =  procCommand.getID()
                cmdList.append( procCommand )
                self.layout.passCommand( cmdList )
                # create lines between self, newprocess, newprocess, newvariable
                procObject = self.layout.getObject( procID )
                ringSource, ringDest = self.layout.thePackingStrategy.autoConnect( self.getID(), procID )
                firstID = self.layout.getUniqueObjectID( OB_PROP_TYPE_CONNECTION )
                firstVarrefName = self.__getNewVarrefID (procObject.getProperty(OB_PROP_FULLID ) )
                firstConnectCommand = lcmds.CreateConnection( self.layout, firstID,  procID, self.id,  ringDest, self.theRingCode, VARIABLE_TO_PROCESS, firstVarrefName )
                
                ringSource, ringDest = self.layout.thePackingStrategy.autoConnect( procID, varID )
                secondID = self.layout.getUniqueObjectID( OB_PROP_TYPE_CONNECTION )
                secondVarrefName = firstVarrefName + "1"
                secondConnectCommand = lcmds.CreateConnection( self.layout, secondID, procID, varID, ringSource, ringDest, PROCESS_TO_VARIABLE, secondVarrefName )
                self.layout.passCommand( [firstConnectCommand] )
                self.layout.passCommand( [secondConnectCommand] )
                self.layout.selectRequest( varID )
            else:    
                # create real line
                variableFullID = self.getProperty( OB_PROP_FULLID )
                procObject = self.layout.getObject(processID)
                processFullID = procObject.getProperty(OB_PROP_FULLID)
                relFullID = ecell.util.getRelativeReference( processFullID, variableFullID )
                #get the process varreflist
                aProFullPN = ecell.util.convertFullIDStringToFullPNString( processFullID, DMINFO_PROCESS_VARREFLIST )
                aVarrefList =  self.getModelEditor().getModel().getEntityProperty( aProFullPN) 
                #filter aVarrefList by variableFullID
                aSpecVarrefList = []
                for aVarref in aVarrefList:
                    if aVarref[ME_VARREF_FULLID] in (variableFullID, relFullID):
                        aSpecVarrefList += [aVarref]
                #get the pro connection obj  
                connectionList = procObject.getProperty(PR_CONNECTIONLIST)

                aSpecDisplayedVarrefList = []
                for conn in connectionList:
                    connObj = self.layout.getObject( conn )
                    varreffName = connObj.getProperty(CO_NAME)
                    varID = connObj.getProperty(CO_VARIABLE_ATTACHED)
                    #get var FUllID
                    if varID != None:
                        varFullID = self.layout.getObject( varID ).getProperty(OB_PROP_FULLID)
                        if varFullID == variableFullID:
                            aSpecDisplayedVarrefList += [varreffName]
                
                
                #check if there is existing varref that hasn't been displayed
                if len(aSpecVarrefList) != len(aSpecDisplayedVarrefList) :
                    for aVarref in aSpecVarrefList:
                        if aVarref[ME_VARREF_NAME] not in aSpecDisplayedVarrefList:
                            newVarrefName = aVarref[ME_VARREF_NAME]
                else:
                    newVarrefName = self.__getNewVarrefID ( processFullID )

                newID = self.layout.getUniqueObjectID( OB_PROP_TYPE_CONNECTION )
                aCommand = lcmds.CreateConnection( self.layout, newID, processID, self.id, 
                        processRing,self.theRingCode,  VARIABLE_TO_PROCESS, newVarrefName )
                self.layout.passCommand( [ aCommand ] )
                # newCon = self.layout.getObject( newID )
                # newCon.checkConnections()
            
    def ringDragged( self, aShapeName, dx, dy ):
        if self.connectionDragged:
            self.theGhostLine.moveEndPoint( dx, dy )
        else:
            self.theRingCode = aShapeName
            
            ( x, y ) = self.getRingPosition( aShapeName )
            x += self.theSD.getRingSize()/2
            y += self.theSD.getRingSize()/2
            self.theGhostLine = GhostLine( self, aShapeName, x+dx, y+dy )
            self.connectionDragged = True

    def getRingSize( self ):
        return self.theSD.getRingSize()

    def getRingPosition( self, ringCode ):
        #return absolute position of ring
        (xRing,yRing) = self.theSD.getShapeAbsolutePosition(ringCode)
        ( x, y ) = self.getAbsolutePosition()
        return (x+xRing, y+yRing )

    def __getNewVarrefID( self, aProcessFullID ):
        aVarrefList = self.layout.layoutManager.theModelEditor.getModel().getEntity( aProcessFullID ).variableReferences
        aVarrefNameSet = Set()
        for aVarref in aVarrefList:
            aVarrefNameSet.add( aVarref.name )
        i = 0
        cand = None
        while True:
            cand = 'X%d' % i
            if cand not in aVarrefNameSet:
                break
            i += 1
        return cand

    def getCursorType( self, aFunction, x, y, buttonPressed ):
        cursorType = EntityObject.getCursorType( self,  aFunction, x, y, buttonPressed  )
        if aFunction == SD_RING and buttonPressed:
            return CU_CONN_INIT
        return cursorType 

class ConnectionObject( EditorObject ):
    def __init__( self, aLayout, objectID, parentObject, aVariableID, aProcessID, aVariableRing, aProcessRing, aVarrefName ):
        EditorObject.__init__( self, aLayout, objectID, parentObject )
        self.properties[ CO_PROCESS_RING ] = aProcessRing
        self.properties[ CO_VARIABLE_RING ] = aVariableRing

        self.properties[ OB_PROP_HAS_FULLID ] = False
        self.properties [ OB_PROP_SHAPE_TYPE ] = SHAPE_TYPE_STRAIGHT_LINE
        self.properties [ CO_LINEWIDTH ] = 3
        self.properties[ OB_PROP_TYPE ] = OB_PROP_TYPE_CONNECTION
        self.properties [ OB_PROP_FILL_COLOR ] = self.layout.graphUtils().getRRGByName("black")
        self.properties[ CO_CONTROL_POINTS ] = None

        #default dimensions
        # get label from processID
        processObj = self.layout.getObject( aProcessID )
        aFullID = processObj.getProperty( OB_PROP_FULLID )
        aVarrefList = self.layout.layoutManager.theModelEditor.getModel().getEntityProperty( identifiers.FullPN( aFullID, DMINFO_PROCESS_VARREFLIST ) )
        aCoef = 0
        for aVarref in aVarrefList:
            if aVarref.name == aVarrefName:
                aCoef = aVarref.coefficient
        self.properties[ CO_NAME ] = aVarrefName
        self.properties[ CO_COEF ] = aCoef
        self.properties[ CO_USEROVERRIDEARROW ] = False
        if type(aProcessID) == type( [] ): #CANNOT BE!!!
            self.properties[ CO_PROCESS_ATTACHED ] = None
            self.properties[ CO_ENDPOINT1 ] = aProcessID
            self.properties[ CO_ATTACHMENT1TYPE ] = OB_NOTHING
            self.properties[ CO_DIRECTION1 ] = self.__getRingDirection( RING_TOP )
        else:
            self.properties[ CO_PROCESS_ATTACHED ] = aProcessID
            aProcessObj = self.layout.getObject ( aProcessID )
            aProcessObj.registerConnection( objectID )
            self.properties[ CO_ENDPOINT1 ] = self.getRingPosition( aProcessID, aProcessRing )
            self.properties[ CO_ATTACHMENT1TYPE ] = OB_PROP_TYPE_PROCESS
            aProcessFullID = aProcessObj.getProperty( OB_PROP_FULLID )
            aModelEditor = self.layout.layoutManager.theModelEditor
            aVarrefList = aModelEditor.getModel().getEntityProperty(
                identifiers.FullPN( aProcessFullID, DMINFO_PROCESS_VARREFLIST ) )
            for aVarref in aVarrefList:
                if aVarref.name == aVarrefName:
                    self.properties[ CO_COEF ] = aVarref.coefficient
                    break
            self.properties[ CO_DIRECTION1 ] = self.__getRingDirection( aProcessRing )
            
        if type(aVariableID) == type( [] ):
            self.properties[ CO_VARIABLE_ATTACHED ] = None
            self.properties[ CO_ENDPOINT2 ] = aVariableID
            self.properties[ CO_ATTACHMENT2TYPE ] = OB_NOTHING
            self.properties[ CO_DIRECTION2 ] = self.__getRingDirection( RING_BOTTOM)
        else:
            self.properties[ CO_VARIABLE_ATTACHED ] = aVariableID
            aVariableObj = self.layout.getObject( aVariableID )
            self.properties[ CO_ENDPOINT2 ] = self.getRingPosition( aVariableID, aVariableRing )
            self.properties[ CO_ATTACHMENT2TYPE ] = OB_NOTHING
            self.properties[ CO_DIRECTION2 ] = self.__getRingDirection( aVariableRing)
            self.properties[ CO_ATTACHMENT2TYPE ] = OB_PROP_TYPE_VARIABLE
            aVariableObj.registerConnection( objectID )
        self.__defineArrowDirection()

        aLineSD = StraightLineSD(self, self.getGraphUtils() )

        self.theSD = aLineSD
        self.properties[ OB_PROP_SHAPE_DESCRIPTOR_LIST ] = aLineSD
        self.theConnectionArrowTypeList = ['Straight','Cornered', 'Curved','MultiBezierCurve']
        self.theConnectionLineTypeList = ['Normal', 'Bold', 'Dashed' ,'Dotted']
        self.hasBeenDragBefore = False
        #Attribute needed for redirectCon
        self.EndPoint2 =self.properties[ CO_ENDPOINT2 ]
        self.processRing = self.properties[ CO_PROCESS_RING ]       

    def __defineArrowDirection( self ):
        self.properties[ CO_HASARROW1 ] = False
        self.properties[ CO_HASARROW2 ] = False
        if self.properties[ CO_COEF ] == 0:
            return
        elif self.properties[ CO_COEF ] <0:
            self.properties[ CO_HASARROW1 ] = True
        else:
            self.properties[ CO_HASARROW2 ] = True

    def arrowheadDragged( self,shapeName, dx, dy, absx, absy ):
        (offsetx, offsety ) = self.getAbsolutePosition()
        x = absx - offsetx
        y = absy - offsety
        if self.outOfRoot( x, y ):
            return 
        if self.theShape.getFirstDrag():
            self.redirectConnection( shapeName, x, y )
            self.theShape.setFirstDrag(False)
            self.hasBeenDragBefore = True

    def redirectConnection( self, shapeName, x, y ):
        if shapeName == ARROWHEAD1:
            self.properties[ CO_ENDPOINT1 ] = [x, y]
        elif shapeName == ARROWHEAD2:
            self.properties[ CO_ENDPOINT2 ] = [x, y]
        self.theShape.repaint()

    def mouseReleased( self, shapeName, x, y ):
        if self.theShape.getFirstDrag():
            self.arrowheadDragged( shapeName, 0, 0, x, y )
        
        if self.hasBeenDragBefore :
            if shapeName == ARROWHEAD2:
                ( varID, varRing ) = self.layout.checkConnection(x, y, DM_TYPE_VARIABLE )
                
                if varID == None:
                    varID = ( x, y)
                    varRing = None
                self.properties[ CO_ENDPOINT2 ]  = self.EndPoint2
                aCommand = lcmds.RedirectConnection( self.layout, self.id, None, varID,None,varRing,None)
                self.layout.passCommand( [aCommand] )
                self.hasBeenDragBefore = False

            elif shapeName == ARROWHEAD1:
                ( proID, processRing ) = self.layout.checkConnection(x, y, DM_TYPE_PROCESS )
                if proID == None or proID != self.properties[ CO_PROCESS_ATTACHED ]:
                    proID = self.properties[ CO_PROCESS_ATTACHED ]
                    processRing = self.properties[ CO_PROCESS_RING ]
                    aProcessObj = self.layout.getObject( proID )
                    (x, y) = aProcessObj.getRingPosition( processRing )
                    rsize = aProcessObj.getRingSize()
                    self.properties[ CO_ENDPOINT1 ] = [ x +rsize/2, y+rsize/2 ]
                    self.theShape.repaint()
                    return 
                else:
                    self.processRing =  processRing
                    aCommand = lcmds.RedirectConnection( self.layout, self.id, proID,None,processRing,None,None)
                    self.layout.passCommand( [aCommand] )
                    self.hasBeenDragBefore = False
            '''
            elif shapeName == SHAPE_TYPE_MULTIBCURVE_LINE:
                self.getArrowType(SHAPE_TYPE_MULTIBPATH_LINE)
                self.properties[CO_CONTROL_POINTS] = theSD.theDescriptorList["MultiBezierCurve"][SD_SPECIFIC]
            '''    

    def redirectConnbyComm(self, aProID,aNewVarID,aProcessRing,aVariableRing,varrefName):
        # arguments are None. means they dont change
        # if newVarId is like [x,y] then i should be detached
        
        if aNewVarID != None:
            # means it changed
            oldVarID = self.properties[ CO_VARIABLE_ATTACHED ]
            if type(aNewVarID) in (type( [] ),type([] )) :
                self.properties[ CO_ENDPOINT2 ] = aNewVarID
                self.properties[ CO_VARIABLE_ATTACHED ] = None
                self.properties[ CO_ATTACHMENT2TYPE ] = OB_NOTHING
                self.properties[ CO_DIRECTION2 ] = self.__getRingDirection( RING_BOTTOM)
            else:
                self.properties[ CO_VARIABLE_ATTACHED ] = aNewVarID
                aVariableObj = self.layout.getObject( aNewVarID)
                (x, y) = aVariableObj.getRingPosition( aVariableRing )

                rsize =  aVariableObj.theSD.getRingSize()/2
                self.properties[ CO_ENDPOINT2 ] = [x + rsize, y+rsize]
                self.properties[ CO_DIRECTION2 ] = self.__getRingDirection( aVariableRing)
                self.properties[ CO_VARIABLE_RING ] = aVariableRing
                self.properties[ CO_ATTACHMENT2TYPE ] = OB_PROP_TYPE_VARIABLE
                aVariableObj.registerConnection(self.id)
                
            if oldVarID != None:
                self.layout.getObject( oldVarID ).unRegisterConnection( self.id )

            self.theShape.repaint() 
            self.EndPoint2 = self.properties[ CO_ENDPOINT2 ]        
        if aProID != None:
            
            if aProcessRing  != None:
                aProcessObj = self.layout.getObject( aProID)
                (x, y) = aProcessObj.getRingPosition( aProcessRing )
                rsize = aProcessObj.getRingSize()
                self.properties[ CO_ENDPOINT1 ] = [ x +rsize/2, y+rsize/2 ]
                self.properties[ CO_DIRECTION1 ] = self.__getRingDirection( aProcessRing )
            self.theShape.repaint() 
            self.properties[  CO_PROCESS_RING ] = self.processRing

    def parentMoved( self, parentID, dx, dy ):
        if parentID == self.properties[ CO_VARIABLE_ATTACHED ]:
            changedType = OB_PROP_TYPE_VARIABLE
        else:
            changedType = OB_PROP_TYPE_PROCESS
        if changedType == self.properties[ CO_ATTACHMENT1TYPE ]:
            chgProp = CO_ENDPOINT1
        else:
            chgProp = CO_ENDPOINT2
        (x, y) = self.properties[ chgProp ]
        x += dx
        y += dy
        self.properties[ chgProp ] = [x, y]
        self.theShape.repaint()

    def __getRingDirection( self, ringCode ):
        if ringCode == RING_TOP:
            return DIRECTION_UP
        elif ringCode == RING_BOTTOM:
            return DIRECTION_DOWN
        elif ringCode == RING_LEFT:
            return DIRECTION_LEFT
        elif ringCode == RING_RIGHT:
            return DIRECTION_RIGHT

    def reconnect( self ):
        aProcessID = self.getProperty( CO_PROCESS_ATTACHED )
        aProcessRing = self.getProperty( CO_PROCESS_RING )
        self.properties[ CO_ENDPOINT1 ] = self.getRingPosition( aProcessID, aProcessRing )
        aVariableID = self.getProperty( CO_VARIABLE_ATTACHED )
        if aVariableID != None:
            aVariableRing = self.getProperty( CO_VARIABLE_RING )        
            self.properties[ CO_ENDPOINT2 ] = self.getRingPosition( aVariableID, aVariableRing )
        self.theShape.repaint()

    def getRingPosition( self, anObjectID, aRing ):
            anObj = self.layout.getObject( anObjectID )
            (x, y) = anObj.getRingPosition( aRing )
            rsize = anObj.getRingSize()
            return [ x +rsize/2, y+rsize/2 ]

    def setProperty(self, aPropertyName, aPropertyValue):
        self.properties[ aPropertyName ] = aPropertyValue
        if aPropertyName == OB_PROP_SHAPE_TYPE:
            if self.theCanvas  != None:
                self.theShape.delete()
            self.getArrowType(aPropertyValue) #hereeee
            if self.theCanvas  != None:
                self.theShape.show()
        elif aPropertyName == CO_NAME:
            if self.theCanvas  != None:
                self.theShape.reName()
        elif aPropertyName == CO_COEF:
            self.__defineArrowDirection()
            if self.theCanvas  != None:
                self.theShape.repaint()
        elif aPropertyName == CO_LINETYPE:
            pass
        elif aPropertyName == CO_LINEWIDTH:
            pass
        elif aPropertyName == CO_HASARROW1:
            pass
        elif aPropertyName == CO_HASARROW2:
            pass
        elif aPropertyName == OB_PROP_FILL_COLOR:
            if self.theCanvas != None:
                self.theShape.fillColorChanged()
        elif aPropertyName == CO_CONTROL_POINTS:
            if self.theCanvas != None:
                self.theShape.repaint()

    def getAvailableArrowType(self):
        return self.theConnectionArrowTypeList

    def getAvailableLineType(self):
        return self.theConnectionLineTypeList

    def getArrowType(self, aShapeType):
        if aShapeType == SHAPE_TYPE_STRAIGHT_LINE:
            aLineSD = StraightLineSD(self, self.getGraphUtils() )
        elif aShapeType == SHAPE_TYPE_CORNERED_LINE:
            aLineSD = corneredLineSD(self, self.getGraphUtils() )
        elif aShapeType == SHAPE_TYPE_CURVED_LINE:
            aLineSD = curvedLineSD(self, self.getGraphUtils() )
        elif aShapeType == SHAPE_TYPE_MULTIBCURVE_LINE:
            aLineSD = multiBcurveLineSD(self, self.getGraphUtils())
            
        self.theSD = aLineSD
        self.properties[ OB_PROP_SHAPE_DESCRIPTOR_LIST ] = aLineSD

        ####### cheCk
        '''
        self.properties[CO_CONTROL_POINTS] = theSD.theDescriptorList["MultiBezierCurve"][SD_SPECIFIC]
        '''

    def show( self ):
        self.theShape = ComplexLine( self, self.theCanvas )
        self.theShape.show()

    def checkConnections( self, end = 2 ):
        # get position of arrowhead 2
        queryProp = CO_ENDPOINT2
        attProp = CO_ATTACHMENT2TYPE

        if end == 1:
            queryProp = CO_ENDPOINT1
            attProp = CO_ATTACHMENT1TYPE
        (x,y) = self.properties[ queryProp ]
        currentAttachment = self.properties[ attProp ]
        if currentAttachment == OB_PROP_TYPE_PROCESS:
            checkFor = OB_PROP_TYPE_PROCESS
        else:
            checkFor = OB_PROP_TYPE_VARIABLE
        ( aShapeID, aRingID ) = self.layout.checkConnection( x, y, checkFor )

    def dispose(self):
        EditorObject.dispose( self )
        varID = self.properties[ CO_VARIABLE_ATTACHED ]
        if varID != None:
            self.layout.getObject( varID ).unRegisterConnection( self.id )
        procID = self.properties[ CO_PROCESS_ATTACHED ]
        self.layout.getObject( procID ).unRegisterConnection( self.id )

    def getMenuItems( self, aSubMenu = None ):
        menuDictList = EditorObject.getMenuItems( self, aSubMenu )
        menuDictList += {
            'delete from layout': self.__userDeleteObject,
            'delete_from_model': self.__userDeleteEntity
            }
        return menuDictList

class TextObject( ConcreteObject ):
    def __init__( self, aLayout, objectID, x, y ):
        # text should be in the aFullID argument
        ConcreteObject.__init__( self, aLayout, objectID, None, x, y )
        self.properties[ OB_PROP_HAS_FULLID ] = False
        self.theObjectMap = {}
        #self.properties [ OB_PROP_SHAPE_TYPE ] = SHAPE_TYPE_TEXT
        self.properties [ OB_PROP_OUTLINE_WIDTH ] = 1
        self.properties[ OB_PROP_TYPE ] = OB_PROP_TYPE_TEXT
        self.theLabel = 'This is a test string for the text box.'
        aTextSD = TextSD(self, self.getGraphUtils(), self.theLabel )
        # first get text width and heigth

        reqWidth = aTextSD.getRequiredWidth()
        reqHeight = aTextSD.getRequiredHeight()

        self.properties [ OB_PROP_DIMENSION_X ] = reqWidth
        if reqWidth<TEXT_MINWIDTH:
            self.properties [ OB_PROP_DIMENSION_X ] = TEXT_MINWIDTH

        self.properties [ OB_PROP_DIMENSION_Y ] = reqHeight
        if reqHeight<TEXT_MINHEIGHT:
            self.properties [ OB_PROP_DIMENSION_Y ] = TEXT_MINHEIGHT

        self.theSD = aTextSD
        self.properties[ OB_PROP_SHAPE_DESCRIPTOR_LIST ] = aTextSD
        self.theTextShapeList = ['Rectangle']

    def resize( self ,  deltaup, deltadown, deltaleft, deltaright  ):
        #first do a resize then a move
        # FIXME! IF ROOTSYSTEM RESIZES LAYOUT MUST BE RESIZED, TOOO!!!!
        # resize must be sum of deltas
        self.properties[ OB_PROP_DIMENSION_X ] += deltaleft + deltaright
        self.properties[ OB_PROP_DIMENSION_Y ] += deltaup + deltadown    

    def reconnect( self ):
        pass

    def getAvailableTextShape(self):
        return self.theTextShapeList



