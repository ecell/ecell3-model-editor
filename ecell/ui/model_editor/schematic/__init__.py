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

from ecell.event import Event, EventDispatcher
import ecell.util
import ecell.identifiers as identifiers

import ecell.ui.model_editor.Utils as utils

class SchematicObjectEvent( Event ):
    pass

class PropertyChangeEvent( SchematicObjectEvent, ModelUpdateEvent ):
    pass

class PropertyDescriptor( object ):
    def __init__( self, name, displayName, description, visible = True, settable = True, gettable = True ):
        self.name = name
        self.displayName = displayName
        self.description = description
        self.visible = visible
        self.settable = settable
        self.gettable = gettable

class PropertySlot( object ):
    def __init__( self, descriptor, value = None ):
        self.descriptor = descriptor
        self.value = None

class ConversionError( RuntimeError ):
    pass

class ColorPropertyDescriptor( PropertyDescriptor ):
    def convertToValue( self, str ):
        if str[ 0 ] != '#':
            raise ConversionError
        return int( str[1: ], 16 )

    def convertToRepr( self, str ):
        if 

class IntegerPropertyDescriptor( PropertyDescriptor ):
    def convertToValue( self, repr ):
        return int( repr )

    def convertToRepr( self, val ):
        return str( val )

class EnumerationEntry( object ):
    def __init__( self, name, displayName, value )
        self.name = name
        self.displayName = displayName
        self.value = value

    def __repr__( self ):
        return self.displayName

class EnumerationPropertyDescriptor( PropertyDescriptor ):
    def __init__( self, name, displayName, description, visible = True, settable = True, gettable = True, list = (,) ):
        PropertyDescriptor.__init__( name, displayName, description, visible, settable, gettable )
        self.list = list

class VectorPropertyDescriptor( PropertyDescriptor ):
    def __init__( self, name, displayName, description, visible = True, settable = True, gettable = True, numOfDims = 0 ):
        PropertyDescriptor.__init__( self, name, displayName, description, visible, settable, gettable, numOfDims )
        self.numOfDims = numOfDims

class PropertySlot( object ):
    def __init__( self, desc, value = None ):
        self.descriptor = desc
        self.annotations = {}
        self.value = value

    def setAnnotation( self, key, val ):
        self.annotations[ key ] = [ val ]

    def addAnnotation( self, key, val ):
        if self.annotations.has_key( key ):
            self.annotations[ key ].append( val )
        else:
            self.annotations[ key ] = [ val ]

    def getAnnotation( self, key ):
        if len( self.annotations[ key ] ) > 1:
            raise RuntimeError, "Annotation %s has multiple entries." % key
        return self.annotations[ key ]

    def getAnnotations( self, key ):
        return self.annotations[ key ]

class SchematicObject( object, EventDispatcher ):
    schematic_props = {}

    class __metaclass__( type );
        def __new__( self, name, bases, dict ):
            retval = type.__new__( self, name, bases, dict )
            propDescriptors = {}
            for base in bases + [ name ]:
                mangledName = '_%s__schematic_props' % base
                if hasattr( base, mangledName ):
                    for desc in getattr( base, mangledName ):
                        propDescriptors[ desc.name ] = desc
            retval.schematic_props = propDescriptors
            return retval

    __schematic_props = (
        VectorPropertyDescriptor(
            'position', 'Position',
            'Position of this object',
            True, True, True, 2
            ),
        PropertyDescriptor(
            'label', 'Label',
            'Label for this object'
            ),
        PropertyDescriptor(
            'strokeColor', 'Stroke Color',
            'Stroke color for this object'
            ),
        PropertyDescriptor(
            'fillColor', 'Fill Color',
            'Fill color for this object'
            ),
        PropertyDescriptor(
            'textColor', 'Text Color',
            'Text color for this object'
            ),
        PropertyDescriptor(
            'shapeType', 'Shape Type',
            'Shape type for this object'
            )
    )

    maxShiftMap = {
        DIRECTION_LEFT:         [ 0 ],
        DIRECTION_RIGHT:        [ 2 ],
        DIRECTION_UP:           [ 1 ],
        DIRECTION_DOWN:         [ 3 ], 
        DIRECTION_BOTTOM_RIGHT: [ 2, 3 ],
        DIRECTION_BOTTOM_LEFT:  [ 0, 3 ],
        DIRECTION_TOP_RIGHT:    [ 2, 1 ],
        DIRECTION_TOP_LEFT:     [ 0, 1 ]
        }

    def __init__( self, id, parentObject ):
        self.id = id
        self.parentObject = parentObject
        self.shapeDescriptor = None
        self.isSelected = False
        self.propertySlots = {}
        self.ox = 0
        self.oy = 0
        self.lastx = 0
        self.lasty = 0
        self.rn = None
        self.totalLabelWidth = 0
        self.labelLimit = 0
        self.theLine = None
        EventDispatcher.__init__( self )
 
        self.setProperties(
            {
                OB_PROP_SHAPE_TYPE    : DEFAULT_SHAPE_NAME,
                OB_PROP_OUTLINE_COLOR : "black",
                OB_PROP_FILL_COLOR    : "white",
                OB_PROP_TEXT_COLOR    : "blue",
                OB_PROP_OUTLINE_WIDTH : 1
                }
            )

    def __setattr__( self, key, val ):
        if key == 'parentObject':
            assert ( val == None and isinstance( self, Layout ) ) \
                   or isinstance( val, EditorObject )
            self.layout = val and val.layout or self
        object.__setattr__( self, key, val )
 
    def getProperty( self, name ):
        if not self.propertyDescriptors.has_key( name ):
            raise KeyError, "Unknown property %s for object %s" % ( name, self.id )
        slot = self.propertySlots.get( aPropertyName, None )
        return slot and slot.value

    def getPropertySlots( self ):
        return self.propertySlots

    def __setProperty( self, name, value ):
        if not self.has_key( self.propertyDescriptors, name ):
            raise KeyError, "Unknown property %s for object %s" % ( name, self.id )
        if self.propertySlots.has_key( name ):
            self.propertySlots[ name ].value = value
        else:
            self.propertySlots[ name ] = PropertySlot(
                self.propertyDescriptors[ name ], value )

    def setProperty( self, name, value ):
        self.setProperties( { name: value } )

    def setProperties( self, properties ):
        propset = {}
        for key, val in properties.iteritems():
            oldValue = self.propertySlots.get( key, None )
            if oldValue != val:
                propset[ key ] = ( val, oldValue )
        self.dispatchEvent(
            PropertyChangeEvent( 'changing', self, values = propset )
        for name, valuePair in propset
            self.__setProperty( name, valuePair[ 0 ] )
        self.dispatchEvent(
            PropertyChangeEvent( 'changed', self, values = propset )

    def getMinDims( self, theType, aLabel ):
        return self.ShapePluginManager.getMinDims(
            theType, OB_PROP_TYPE_DEFAULT, self.getGraphUtils(), aLabel )
        
    def dispose( self ):
        pass

    def hide( self ):
        # deletes it from canvas
        pass

    #def doSelect( self, shift_pressed = False ):
    #    self.layout.selectRequest( self.id, shift_pressed )

    def handleViewObjectEvent( self, ev ):
        pass

    def popupEditor( self ):
        self.layout.popupObjectEditor( self.id )      

    def setLimits( self, x0, y0, x1, y1 ):
        pass

    def show( self ):
        pass

    def showLine(self):
        self.theLine = ComplexLine()

    def getCursorType( self, aFunction, x, y, buttonPressed ):
        if aFunction in [ SD_FILL, SD_TEXT ] and buttonPressed:
            return CU_MOVE
        elif aFunction  in [ SD_FILL, SD_TEXT ] and not buttonPressed:
            return CU_POINTER
        return CU_POINTER

    def adjustCanvas(self,dx,dy):
        if self.theCanvas.getBeyondCanvas():
            self.parentObject.theCanvas.setCursor(CU_MOVE)
            self.parentObject.theCanvas.scrollTo(dx,dy)
            self.parentObject.theCanvas.setLastCursorPos(dx,dy)

    def getDirectionShift(self,dx,dy):
        if dx>0 and dy ==0:
            return DIRECTION_RIGHT
        if dx<0 and dy ==0:
            return DIRECTION_LEFT
        if dy>0 and dx ==0:
            return DIRECTION_DOWN
        if dy<0 and dx ==0:
            return DIRECTION_UP
        if dx>0 and dy>0:
            return DIRECTION_BOTTOM_RIGHT
        if dx<0 and dy>0:
            return DIRECTION_BOTTOM_LEFT
        if dx>0 and dy<0:
            return DIRECTION_TOP_RIGHT
        if dx<0 and dy<0:
            return DIRECTION_TOP_LEFT

    def adjustLayoutCanvas(self,dup,ddown,dleft,dright):
        scrollx = self.layout.getProperty(LO_SCROLL_REGION)[0]
        scrolly = self.layout.getProperty(LO_SCROLL_REGION)[1]
        scrollx2 = self.layout.getProperty(LO_SCROLL_REGION)[2]
        scrolly2 = self.layout.getProperty(LO_SCROLL_REGION)[3]
        dleft = -dleft
        dup = -dup
        scrollx += dleft
        scrolly += dup
        scrollx2 += dright
        scrolly2 += ddown
        self.layout.setProperty(LO_SCROLL_REGION,[scrollx,scrolly,scrollx2,scrolly2])
        self.layout.setProperty(OB_PROP_DIMENSION_X,scrollx2 - scrollx)
        self.layout.setProperty(OB_PROP_DIMENSION_Y,scrolly2 - scrolly)
        if self.layout.getCanvas() != None:
            self.layout.getCanvas().setSize(self.layout.getProperty(LO_SCROLL_REGION))
            self.layout.getCanvas().scrollTo(dleft+dright,ddown+dup) 

    def canPaste(self):
        return False

    def pasteObject(self):
        pass

    def getParent( self ):
        return self.parentObject

    def getModelEditor( self ):
        return self.layout.layoutManager.theModelEditor

    def __test(self, *args ):
        pass

    def __userDeleteObject( self, *args ):
        aCommandList = []
        self.theMenu.dispose()
        self.layout.deleteSelected()

    def __userDeleteEntity ( self, *args ):

        self.theMenu.dispose()
        self.layout.deleteEntities()

    def __undo(self, *args ):
        self.getModelEditor().undoCommandList()

    def __redo(self, *args ):
        self.getModelEditor().redoCommandList()
        GraphUtils

    def __cut(self,*args):
        
        self.__copy( None )
        self.__userDeleteEntity( None )
        
    def __copy(self,*args):
        
        if isinstance( self.parentObject, Layout ):
            aLayoutManager = self.getModelEditor().layoutManager
            self.LayoutBufferFactory =  LayoutBufferFactory(self.getModelEditor(), aLayoutManager)
            self.aLayoutBuffer = self.LayoutBufferFactory.createMultiObjectBuffer(self.layout.theName, \
                    self.layout.theSelectedObjectIDList )
            self.getModelEditor().setCopyBuffer(self.aLayoutBuffer )

    def __paste(self,*args):
        self.pasteObject()

    def __userCreateConnection(self,*args):
        if self.getProperty(OB_PROP_TYPE) == OB_PROP_TYPE_PROCESS:
            if len(args) == 0:
                return None
            if type( args[0] ) == gtk.MenuItem:
                variableID = args[0].get_name()
            varrefName = variableID.split(',')[1]
            variableID = variableID.split(',')[2]
            newID = self.layout.getUniqueObjectID( OB_PROP_TYPE_CONNECTION )
            (processRing, variableRing) = self.thePackingStrategy.autoConnect(self.id, variableID )
            aCommand = lcmds.CreateConnection( self.layout, newID,  self.id,variableID, processRing, variableRing, PROCESS_TO_VARIABLE, varrefName )
            
            self.layout.passCommand([aCommand])
        
            

        if self.getProperty(OB_PROP_TYPE) ==OB_PROP_TYPE_VARIABLE:
            aVariableFullID = self.getProperty( OB_PROP_FULLID )
            if len(args) == 0:
                return None
            if type( args[0] ) == gtk.MenuItem:
                processID = args[0].get_name()
            aProcessFullID = processID.split(',')[0]
            processID = processID.split(',')[1]

            #get var reff name
            aModelEditor = self.getModelEditor()
            aVarReffList = aModelEditor.theModel.getEntityProperty(
                identifiers.FullPN( aProcessFullID, DMINFO_PROCESS_VARREFLIST ) )
            varReffNameList = []
            for i in range (len(aVarReffList)):
                varFullID= ecell.util.getAbsoluteReference(aProcessFullID, aVarReffList[i][ME_VARREF_FULLID])
                if aVariableFullID == varFullID:
                    varReffNameList += [aVarReffList[i][ME_VARREF_NAME]]
            for avarRefName in varReffNameList:
                newID = self.layout.getUniqueObjectID( OB_PROP_TYPE_CONNECTION )
                (processRing, variableRing) = self.thePackingStrategy.autoConnect( processID, self.id )
                aCommand = lcmds.CreateConnection( self.layout, newID,  processID,self.id, processRing, variableRing, PROCESS_TO_VARIABLE, avarRefName )
                self.layout.passCommand(  [aCommand]  )  
               
    def __userCreateObject(self,*args):
        
        (offsetx, offsety ) = self.getAbsolutePosition()
        x = self.newObjectPosX - (self.theSD.insideX + offsetx )
        y = self.newObjectPosY - ( self.theSD.insideY + offsety )

        
        aModelEditor = self.layout.layoutManager.theModelEditor
        
        
        
        if len(args) == 0:
            return None
        if type( args[0] ) == gtk.MenuItem:
            anEntityName = args[0].get_name()

        aFullID = anEntityName
        objectType = aFullID.typeCode
        objectID = self.layout.getUniqueObjectID( objectType )
        
         
        #create aCommand
        aCommand = None
    
        if not aFullID in self.existobjectFullIDList:
            aCommand = lcmds.CreateObject( self.layout, objectID, objectType, aFullID, x,y, self )         
                

        if aCommand != None:
            px2 = self.getProperty(OB_PROP_DIMENSION_X)
            py2 = self.getProperty(OB_PROP_DIMENSION_Y)
            rpar = n.array([0,0,px2,py2])
            if objectType == OB_PROP_TYPE_SYSTEM:
                rn = self.createRnAddSystem()
                minreqx, minreqy = self.getMinDims( DM_TYPE_SYSTEM, aFullID )
                x2 = x+max( SYS_MINWIDTH, minreqx )
                y2 = y+max( SYS_MINHEIGHT, minreqy )
                availspace = self.getAvailSpace(x,y,x2,y2,rn)
                self.availSpace = availspace
                # check boundaries
                if (not self.isOverlap(x,y,x2,y2,rn) and self.isWithinParent(x,y,x2,y2,rpar)):
                    self.layout.passCommand( [aCommand] )
                    
            if objectType == OB_PROP_TYPE_PROCESS:
                minreqx, minreqy = self.getMinDims( DM_TYPE_PROCESS, aFullID.id )
                x2 = x+max( PRO_MINWIDTH, minreqx )
                y2 = y+max( PRO_MINHEIGHT, minreqy )
                rn = self.createRnAddOthers()
                if (not self.isOverlap(x,y,x2,y2,rn) and self.isWithinParent(x,y,x2,y2,rpar)):
                    self.layout.passCommand( [aCommand] )

            if objectType == OB_PROP_TYPE_VARIABLE:
                minreqx, minreqy = self.getMinDims( DM_TYPE_VARIABLE, aFullID.split(":")[2] )
                x2 = x+max( VAR_MINWIDTH, minreqx )
                y2 = y+max( VAR_MINHEIGHT, minreqy )
                # check boundaries
                rn = self.createRnAddOthers()
                if (not self.isOverlap(x,y,x2,y2,rn) and self.isWithinParent(x,y,x2,y2,rpar)):
                    self.layout.passCommand( [aCommand] )
                    
            else:
                pass

    def setExistObjectFullIDList(self):
        #get the existing objectID in the System
        exsistObjectInTheLayoutList = []
        if self.getProperty(OB_PROP_HAS_FULLID):
            exsistObjectInTheLayoutList =self.getObjectList()

        #get the object FullID exist in the layout using its objectID
        for anID in exsistObjectInTheLayoutList:
            object = self.layout.getObject(anID)
            objectFullID = object.getProperty(OB_PROP_FULLID)
            self.existobjectFullIDList += [objectFullID]

    def createRnOut(self):
        no = len(self.parentObject.getObjectList())
        rn = None
        if no>1:
            for sib in self.parentObject.getObjectList():
                asib = self.parentObject.getObject(sib)
                if (asib.getProperty(OB_PROP_FULLID) != self.getProperty(OB_PROP_FULLID)) and (asib.getProperty(OB_PROP_TYPE) ==OB_PROP_TYPE_SYSTEM):
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
    
    def isOverlap(self,x1,y1,x2,y2,rn):
        r1 = n.array([x1,y1,x2,y2])
        r1 = n.reshape(r1,(4,1))
        if rn != None:
            return self.getGraphUtils().calcOverlap(r1,rn)
        else:
            return False
        
    def isWithinParent(self,u1,v1,u2,v2,rpar):
        rpar = n.reshape(rpar,(4,1))
        olw = self.getProperty( OB_PROP_OUTLINE_WIDTH )
        #v2 += olw*8 #height of the parent label
        r2 = n.array([u1,v1,u2,v2])
        r2 = n.reshape(r2,(4,1))
        return self.getGraphUtils().calcWithin(rpar,r2)

    def getGraphUtils( self ):
        return self.layout.graphUtils()

    def buttonReleased( self ):
        pass

    def createRparent(self):
        olw = self.propertySlots[ OB_PROP_OUTLINE_WIDTH ]
        if isinstance( self.parentObject, Layout ):
            x1 = 0
            y1 = 0
            x2= x1+self.parentObject.getProperty(OB_PROP_DIMENSION_X)
            y2= y1+self.parentObject.getProperty(OB_PROP_DIMENSION_Y)
        else:
            x1 = 0
            #y1 = self.parentObject.getProperty(OB_PROP_DIMENSION_Y)-self.parentObject.getProperty
#(SY_INSIDE_DIMENSION_Y)
            y1 = 0
            x2= x1+self.parentObject.getProperty(SY_INSIDE_DIMENSION_X)
            y2= y1+self.parentObject.getProperty(SY_INSIDE_DIMENSION_Y)
        r1 = n.array([x1,y1,x2,y2])
        return r1  
    
    def estLabelWidth(self,newLabel):
        pass

    def getAvailableShapes( self ):
        return self.ShapePluginManager.getShapeList(
            self.getProperty( OB_PROP_TYPE ) )
    
    def setLabelParam(self,totalWidth,limit):
        self.totalLabelWidth = totalWidth
        self.totalLimit = limit

    def getLabelParam(self):
        return self.totalLabelWidth,self.totalLimit

    def calcLabelParam(self,label):
        estWidth = self.estLabelWidth(label)
        newx2 = estWidth
        #check overlap and within parent
        x = self.getProperty(OB_PROP_POS_X)
        x2 = self.getProperty(OB_PROP_DIMENSION_X)
        totalWidth = x+newx2
        maxShift = self.getMaxShiftPos(DIRECTION_RIGHT)
        limit = x+x2+maxShift
        self.setLabelParam(totalWidth,limit)
        return maxShift + x2

    def truncateLabel(self,aLabel,lblWidth,dimx):
        truncatedLabel = self.getGraphUtils().truncateLabel(aLabel,lblWidth,dimx,self.getProperty(OB_PROP_MIN_LABEL))
        return truncatedLabel

    def getMaxShiftPos(self,direction):
        dir = direction
        olw = self.getProperty(OB_PROP_OUTLINE_WIDTH)
        x1 = self.getProperty(OB_PROP_POS_X)
        y1 = self.getProperty(OB_PROP_POS_Y)
        x2 = x1+self.getProperty(OB_PROP_DIMENSION_X)
        y2 = y1+self.getProperty(OB_PROP_DIMENSION_Y)
        r1 = n.array([x1,y1,x2,y2])
        rn = self.createRnOut()
        rpar = self.createRparent()
        matrix = self.getGraphUtils().calcMaxShiftPos(r1,rn,dir,rpar)
        mshift = matrix-r1
        mshift = mshift * n.array( [-1,-1,1,1] )
        if len(self.maxShiftMap[dir])>1:
            posx,posy = self.maxShiftMap[dir][0],self.maxShiftMap[dir][1]
            return max(0, mshift[posx] ), max(0, mshift[posy] )
        else:
            pos = self.maxShiftMap[dir][0]
            return max(0, mshift[pos] )
