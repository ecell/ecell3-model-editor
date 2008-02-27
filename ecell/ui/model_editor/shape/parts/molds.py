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

__all__ = (
    'PartMold',
    'ShapePartMold',
    'BezierPathPartMold',
    'LinearPartMold',
    'PolylinePartMold',
    'PolygonPartMold',
    'TextPartMold',
    'RectanglePartMold',
    'EllipsePartMold',
    'ImagePartMold',
    'PartMolds',
    'ExprCompiler',
    'StandardMoldsBuilder',
    )

class PartMold( object ):
    __slots__ = (
        'id',
        'parent',
        'function',
        'shape',
        'dynamic',
        'below',
        'above'
        )

    def __init__( self, id = None, parent = None, function = None ):
        self.id = id
        self.parent = parent
        self.function = function
        self.dynamic = False
        self.below = None
        self.above = None
        self.shape = None

    def __getitem__( self, key ):
        return getattr( self, key )

    def has_key( self, key ):
        return hasattr( self, key )

class ShapePartMold( PartMold ):
    __slots__ = (
        'strokeColor',
        'fillColor',
        'strokeWidth'
        )

    def __init__( self, id = None, parent = None, function = None, strokeColor = None, fillColor = None, strokeWidth = None):
        PartMold.__init__( self, id, parent, function )
        self.strokeColor = strokeColor
        self.fillColor = fillColor
        self.strokeWidth = strokeWidth

class BezierPathPartMold( ShapePartMold ):
    __slots__ = (
        'path',
        )

    def __init__( self, id = None, parent = None, function = None, strokeColor = None, fillColor = None, strokeWidth = None, path = None ):
        ShapePartMold.__init__( self, id, parent, function, strokeColor, fillColor, strokeWidth )
        self.path = path

class LinearPartMold( PartMold ):
    __slots__ = (
        'color',
        )

    def __init__( self, id = None, parent = None, function = None, color = None ):
        PartMold.__init__( self, id, parent, function )
        self.color = color

class PolylinePartMold( LinearPartMold ):
    __slots__ = (
        'width',
        'points',
        )

    def __init__( self, id = None, parent = None, function = None, color = None, width = None, points = None ):
        LinearPartMold.__init__( self, id, function, color )
        self.width = width
        self.points = points

class PolygonPartMold( ShapePartMold ):
    __slots__ = (
        'points',
        )

    def __init__( self, id = None, parent = None, function = None, strokeColor = None, fillColor = None, strokeWidth = None, points = None ):
        ShapePartMold.__init__( self, id, parent, function, strokeColor, fillColor, strokeWidth )
        self.points = points

class TextPartMold( LinearPartMold ):
    __slots__ = (
        'pos',
        'anchor',
        'text',
        'font',
        )

    def __init__( self, id = None, parent = None, function = None, color = None, pos = None, anchor = None, font = None, text = None ):
        LinearPartMold.__init__( self, id, parent, function, color )
        self.pos = pos
        self.anchor = anchor
        self.font = font
        self.text = text

class RectanglePartMold( ShapePartMold ):
    __slots__ = (
        'rect',
        )

    def __init__( self, id = None, parent = None, function = None, strokeColor = None, fillColor = None, strokeWidth = None, rect = None ):
        ShapePartMold.__init__( self, id, parent, function, strokeColor, fillColor, strokeWidth )
        self.rect = rect

class EllipsePartMold( ShapePartMold ):
    __slots__ = (
        'rect',
        )

    def __init__( self, id = None, parent = None, function = None, strokeColor = None, fillColor = None, strokeWidth = None, rect = None ):
        ShapePartMold.__init__( self, id, parent, function, strokeColor, fillColor, strokeWidth )
        self.rect = rect

class ImagePartMold( PartMold ):
    __slots__ = (
        'pos',
        'anchor',
        'pixbuf',
        )

    def __init__( self, id = None, parent = None, function = None, pos = None, anchor = None, pixbuf = None ):
        PartMold.__init__( self, id, parent, function )
        self.pos = pos,
        self.anchor = anchor
        self.pixbuf = pixbuf

class PartMolds( PartMold ):
    __slots__ = (
        'children',
        'items',
        'pos',
        'size'
        )

    def __init__( self, id = None, parent = None, function = None, pos = ( 0, 0 ), size = None ):
        PartMold.__init__( self, id, parent, function )
        self.children = []
        self.items = {}
        self.pos = pos
        self.size = size

    def __getitem__( self, key ):
        if self.items.has_key( key ):
            return self.items[ key ]
        return PartMold.__getitem__( self, key )

    def __setitem__( self, key, val ):
        self.items[ key ] = val

    def has_key( self, key ):
        return self.items.has_key( key ) or PartMold.has_key( self, key )

    def __iter__( self ):
        return children.__iter__()

    def append( self, item ):
        self.children.append( item )
        if item.id:
            self.items[ item.id ] = item
        if item.dynamic:
            self.dynamic = True

class ExprCompiler:
    def __init__( self, expr ):
        self.dynamic = False
        self.expr = expr

    def compile( self ):
        self.result = self.__compile( self.expr )
        return self

    def __compile( self, val ):
        if isinstance( val, list ) or isinstance( val, tuple ):
            return [ self.__compile( _val ) for _val in val ]
        if isinstance( val, str ) and val[ 0: 5 ] == 'code:':
            self.dynamic = True
            return compile( val[ 5: ], '<partattr> ' + val[ 5: ], 'eval' )
        else:
            return val

class StandardMoldsBuilder( object ):
    def build( self, data ):
        parts = PartMolds()
        for key in data.iterkeys():
            if key == 'type' or key == 'parts':
                continue
            c = ExprCompiler( data[ key ] )
            c.compile()
            try:
                setattr( parts, key, c.result )
                parts.dynamic |= c.dynamic
            except:
                assert not c.dynamic
                parts[ key ] = data[ key ]

        for repr in data[ 'parts' ]:
            if repr[ 'type' ] == 'group':
                part = self.build( repr )
            else:
                part = __import__( __name__, globals(), locals(), [ 'dummy' ] ).__dict__[ repr[ 'type' ] + 'PartMold' ]( parent = parts )
                for key in repr.iterkeys():
                    if key == 'type':
                        continue
                    c = ExprCompiler( repr[ key ] )
                    c.compile()
                    part.dynamic |= c.dynamic
                    setattr( part, key, c.result )
            parts.append( part )
        return parts


