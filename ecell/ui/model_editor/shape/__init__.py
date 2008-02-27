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

from weakref import WeakKeyDictionary, ref
from ecell.event import Event, EventDispatcher, Observable
from ecell.ui.model_editor.shape.parts import *
from ecell.ui.model_editor.shape.parts.molds import *
from ecell.ui.model_editor.shape.parts.renderer import Renderer

__all__ = (
    'Shape',
    'ShapeEvent',
    'ShapeManager',
    'ComplexShape',
    'Connector'
    )

class ShapeEvent( Event ):
    pass

class ModelUpdateEvent( Event ):
    __slots__ = (
        'values',
        )

class ValueAccessor( dict ):
    def __init__( self, *objs ):
        self.objs = objs

    def has_key( self, key ):
        for obj in self.objs:
            if obj == None:
                continue
            if obj.has_key( key ):
                return True
        return False

    def __getitem__( self, key ):
        for obj in self.objs:
            if obj == None:
                continue
            if obj.has_key( key ):
                return obj[ key ]
        raise KeyError, key

class ShapeManager( object ):
    def __init__( self, canvas ):
        self.canvasItemToPartMap = WeakKeyDictionary()
        self.canvasItemToShapeMap = WeakKeyDictionary()
        self.canvas = canvas

    def associateCanvasItemWithShape( self, canvasItem, shape ):
        self.canvasItemToShapeMap[ canvasItem ] = ref( shape )

    def associateCanvasItemWithPart( self, canvasItem, part ):
        self.canvasItemToPartMap[ canvasItem ] = mrt

    def getPartByCanvasItem( self, canvasItem ):
        return self.canvasItemToPartMap.get( canvasItem, None )

    def getShapeByCanvasItem( self, canvasItem ):
        r = self.canvasItemToShapeMap.get( canvasItem, None )
        if r != None:
            return r()
        return None

    def createComplexShape( self, molds, modelObject = None ):
        return ComplexShape( self, self.canvas, molds, modelObject )

    def createConnector( self, modelObject = None ):
        return Connector( self, self.canvas, modelObject )

class Shape:
    __slots__ = (
        'canvas',
        'manager'
        )

    def update( self ):
        raise NotImplementedError

    def dispose( self ):
        raise NotImplementedError

class ComplexShape( object, Shape, EventDispatcher ):
    def __init__( self, manager, canvas, molds, modelObject = None ):
        assert modelObject == None or isinstance( modelObject, Observable )
        EventDispatcher.__init__( self )
        object.__setattr__( self, 'canvas', canvas )
        object.__setattr__( self, 'manager', manager )
        object.__setattr__( self, 'props', { 'rect': ( 0, 0, 0, 0 ) } )
        object.__setattr__( self, 'idToPartMap', {} )
        object.__setattr__( self, 'functionToPartsMap', {} )
        object.__setattr__( self, 'moldToPartMap', {} )
        object.__setattr__( self, 'molds', None )
        object.__setattr__( self, 'modelObject', None )
        object.__setattr__( self, 'parts', None )
        object.__setattr__( self, 'disposed', False )
        _molds = PartMolds(
            molds.id,
            molds.parent,
            molds.function,
            (
                ExprCompiler( "code:props['rect'][ 0 ]" ).compile().result,
                ExprCompiler( "code:props['rect'][ 1 ]" ).compile().result
                ),
            (
                ExprCompiler( "code:props['rect'][ 2 ]" ).compile().result,
                ExprCompiler( "code:props['rect'][ 3 ]" ).compile().result
                ) )
        _molds.dynamic = True
        _molds.children = molds.children[:]
        self.modelObject = modelObject
        self.molds = _molds

    def __setattr__( self, key, val ):
        if key == 'molds':
            rdr = Renderer( None, self.manager, self, self.canvas )
            object.__setattr__( self, 'parts', rdr.render( val ) )
            object.__setattr__( self, 'idToPartMap',
                    rdr.idToPartMap )
            object.__setattr__( self, 'functionToPartsMap',
                    rdr.functionToPartsMap )
            object.__setattr__( self, 'moldToPartMap',
                    rdr.moldToPartMap )
            object.__setattr__( self, key, val )
        elif key == 'modelObject':
            if self.modelObject and isinstance( self.modelObject, Observable ):
                self.modelObject.removeObserver( self )
            if val != None:
                if isinstance( val, Observable ):
                    val.addObserver(
                        ModelUpdateEvent, self.__handleModelUpdateEvent )
                for k, v in val.iteritems():
                    self[ k ] = v
            object.__setattr__( self, key, val )
        else:
            return object.__setattr__( self, key, val )

    def __setitem__( self, key, val ):
        if key == 'pos':
            self.props[ 'rect' ] =  (
                val[ 0 ], val[ 1 ],
                self.props[ 'rect' ][ 2 ], self.props[ 'rect' ][ 3 ],
                )
            self.update()
            return
        elif key == 'size':
            self.props[ 'rect' ] =  (
                self.props[ 'rect' ][ 0 ], self.props[ 'rect' ][ 1 ],
                val[ 0 ], val[ 1 ],
                )
            self.update()
            return
        elif key == 'rect':
            if self.molds != None:
                self.parts.pos = val[ 0: 2 ]
                self.parts.size = val[ 2: 4 ]
            self.update()
        self.props[ key ] = val

    def __getitem__( self, key ):
        if key == 'pos':
            return self.props[ 'rect' ][ 0: 2 ]
        elif key == 'size':
            return self.props[ 'rect' ][ 2: 4 ]
        return self.props[ key ]

    def getPartsByFunction( self, func ):
        return self.functionToPartsMap.get( func, None )

    def getPartByID( self, id ):
        return self.idToPartMap.get( id, None )

    def update( self ):
        for holder in self.moldToPartMap.itervalues():
            holder.update()

    def evalParameter( self, holder, expr ):
        if holder.mold.dynamic:
            if expr.__class__.__name__ == 'code':
                return eval( expr, {
                        'props': self.props
                        },
                    ValueAccessor(
                        holder,
                        holder.parent,
                        self.idToPartMap,
                        self.props ) )
            elif isinstance( expr, list ) or isinstance( expr, tuple ):
                return [ self.evalParameter( holder, i ) for i in expr ]
        return expr

    def handleCanvasEvent( self, part, ev ):
        self.dispatchEvent(
            ShapeEvent(
                part.mold.function, self, part = part, canvasEvent = ev ) )

    def __handleModelUpdateEvent( self, ev ):
        if ev.type == 'changed':
            for key, val in ev.values.iteritems():
                self[ key ] = val[ 0 ]
            self.update()

    def dispose( self ):
        if self.disposed:
            return
        self.molds.canvasItem.dispose()
        self.dispatchEvent( ShapeEvent( 'disposed', self ) )
        object.__setattr__( self, 'disposed', True )

CONNECTOR_ORI_VERTICAL = 0
CONNECTOR_ORI_HORIZONTAL = 1

class Connector( object, Shape, EventDispatcher ):
    def __init__( self, manager, canvas, modelObject = None ):
        assert modelObject == None or isinstance( modelObject, Observable )
        EventDispatcher.__init__( self )
        object.__setattr__( self, 'manager', manager )
        object.__setattr__( self, 'canvas', canvas )
        object.__setattr__( self, 'canvasItem', None )
        object.__setattr__( self, 'disposed', False )
        object.__setattr__( self, 'modelObject', None )
        object.__setattr__( self, 'props', {
            'rect': ( 0, 0, 0, 0 ),
            'orientation': CONNECTOR_ORI_VERTICAL,
            'color': 0x808080ff,
            } )
        self.modelObject = modelObject

    def __setattr__( self, key, val ):
        if key == 'modelObject':
            if self.modelObject and isinstance( self.modelObject, Observable ):
                self.modelObject.removeObserver( self )
            if val != None:
                if isinstance( val, Observable ):
                    val.addObserver(
                        ModelUpdateEvent, self.__handleModelUpdateEvent )
                for k, v in val.iteritems():
                    self[ k ] = v
            object.__setattr__( self, key, val )
        else:
            return object.__setattr__( self, key, val )

    def has_key( self, key ):
        return self.props.has_key( key ) or \
            key == 'pos' or \
            key == 'start' or \
            key == 'end' or \
            key == 'size'

    def __setitem__( self, key, val ):
        if key == 'pos' or key == 'start':
            self.props[ 'rect' ] =  (
                val[ 0 ], val[ 1 ],
                self.props[ 'rect' ][ 2 ], self.props[ 'rect' ][ 3 ],
                )
            return
        elif key == 'end':
            self.props[ 'rect' ] =  (
                self.props[ 'rect' ][ 0 ], self.props[ 'rect' ][ 1 ],
                self.props[ 'rect' ][ 0 ] + val[ 0 ],
                self.props[ 'rect' ][ 1 ] + val[ 1 ],
                )
        elif key == 'size':
            self.props[ 'rect' ] =  (
                self.props[ 'rect' ][ 0 ], self.props[ 'rect' ][ 1 ],
                val[ 0 ], val[ 1 ],
                )
            return
        self.props[ key ] = val

    def __getitem__( self, key ):
        if key == 'pos' or key == 'start':
            return self.props[ 'rect' ][ 0: 2 ]
        elif key == 'end':
            return (
                self.props[ 'rect' ][ 0 ] + self.props[ 'rect' ][ 2 ],
                self.props[ 'rect' ][ 1 ] + self.props[ 'rect' ][ 3 ]
                )
        elif key == 'size':
            return self.props[ 'rect' ][ 2: 4 ]
        return self.props[ key ]

    def __handleModelUpdateEvent( self, ev ):
        if ev.type == 'changed':
            for key, val in ev.values.iteritems():
                self[ key ] = val[ 0 ]
            self.update()

    def update( self ):
        rect = self.props[ 'rect' ]
        if self.props[ 'orientation' ] == CONNECTOR_ORI_VERTICAL:
            points = (
                ( rect[ 0 ], rect[ 1 ] ),
                ( rect[ 0 ], rect[ 1 ] + rect[ 3 ] / 2 ),
                ( rect[ 0 ] + rect[ 2 ], rect[ 1 ] + rect[ 3 ] / 2 ),
                ( rect[ 0 ] + rect[ 2 ], rect[ 1 ] + rect[ 3 ] ),
                )
        elif self.props[ 'orientation' ] == CONNECTOR_ORI_HORIZONTAL:
            points = (
                ( rect[ 0 ], rect[ 1 ] ),
                ( rect[ 0 ] + rect[ 2 ] / 2, rect[ 1 ] ),
                ( rect[ 0 ] + rect[ 2 ] / 2, rect[ 1 ] + rect[ 3 ] ),
                ( rect[ 0 ] + rect[ 2 ], rect[ 1 ] + rect[ 3 ] ),
                )
        params = {
            'points': points,
            'color': self.props[ 'color' ],
            'arrowSpec': { 'length': 4, 'tipLength': 4, 'width': 3 },
            'startArrow': False,
            'endArrow': True,
            'width': 2
            }
        if self.canvasItem == None:
            self.canvasItem = self.canvas.drawPolyline( **params )
            self.manager.associateCanvasItemWithShape( self.canvasItem, self )
        else:
            for key, val in params.iteritems():
                setattr( self.canvasItem, key, val ) 
            self.canvasItem.update()

    def dispose( self ):
        if self.disposed:
            return
        self.canvasItem.dispose()
        self.dispatchEvent( ShapeEvent( 'disposed', self ) )
        self.disposed = True

