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

import ecell.ui.model_editor.viewobjects as viewobjs
from ecell.ui.model_editor.command import *

class ModelCommand( AtomicCommand ):
    pass

class EntityCommand( ModelCommand ):
    __slots__ = [ 'fullID' ]
    def __init__( self, **operands ):
        assert 'fullID' in operands
        AtomicCommand.__init__( self, **operands )

class CreateEntity( EntityCommand ):
    def __repr__( self ):
        return 'create entity [%s]' % self.fullID

class DeleteEntity( EntityCommand ):
    def __repr__( self ):
        return 'delete entity [%s]' % self.fullID

class ChangeEntityClass( EntityCommand ):
    __slots__ = [ 'className' ]

    def __repr__( self ):
        return 'change class of entity [%s] to [%s]' % (
            self.fullID, self.className )

class ChangeEntityProperty( EntityCommand ):
    __slots__ = [ 'propertyName' ]

    def __repr__( self ):
        return 'change property [%s] of entity [%s]' % (
            self.propertyName, self.fullID )

class CreateEntityProperty( EntityCommand ):
    __slots__ = [ 'propertyName' ]

    def __repr__( self ):
        return 'create property [%s] in entity [%s]' % (
            self.propertyName, self.fullID )

class DeleteEntityProperty( EntityCommand ):
    __slots__ = [ 'propertyName' ]

    def __repr__( self ):
        return 'delete property [%s] of entity [%s]' % (
            self.propertyName, self.fullID )

class RenameEntityProperty( EntityCommand ):
    __slots__ = [ 'propertyName', 'newPropertyName' ]

    def __repr__( self ):
        return 'rename property [%s] of entity [%s] to [%s]' % (
            self.propertyName,
            self.fullID,
            self.newPropertyName )

class SetEntityInfo( EntityCommand ):
    __slots__ = [ 'info' ]

    def __repr__( self ):
        return 'annotate entity [%s] with "%s"' % ( self.fullID, self.info )

class MoveEntity( EntityCommand ):
    __slots__ = [ 'newFullID' ]

    def __init__( self, *args, **nargs ):
        EntityCommand.__init__( self, *args, **nargs )
        assert self.newFullID.typeCode == self.fullID.typeCode

    def __repr__( self ):
        return 'move entity [%s] to [%s]' % ( self.fullID, self.newFullID )

class AddVariableReference( EntityCommand ):
    __slots__ = [ 'variableFullID', 'id', 'coefficient' ]

    def __repr__( self ):
        return 'add variable reference [id=%s, fullID=%s, coef=%s] to entity [%s]' % (
            self.id, self.variableFullID, self.coefficient, self.fullID )

class DeleteVariableReference( EntityCommand ):
    __slots__ = [ 'id' ]

    def __repr__( self ):
        return 'delete variable reference [id=%s] from entity [%s]' % (
            self.id, self.fullID )

class ChangeVariableReference( EntityCommand ):
    __slots__ = [ 'fullID', 'id', 'component', 'value' ]

    def __repr__( self ):
        return 'change [%s] of variable reference [id=%s] of entity [%s]' % (
            self.component, self.id, self.fullID )

class LayoutCommand( AtomicCommand ):
    __slots__ = [ 'layoutID' ]

class CreateLayout( LayoutCommand ):
    pass

class DeleteLayout( LayoutCommand ):
    pass

class RenameLayout( LayoutCommand ):
    __slots__ = [ 'newLayoutID' ]

class CreateViewObject( LayoutCommand ):
    __slots__ = [ 'id', 'type', 'properties' ]

    def prerequisite( self, runner ):
        if issubclass( self.type, viewobjs.EntityObject ):
            assert self.properties.has_key( 'fullID' )
            fullID = self.properties.has_key( 'fullID' )
            if self.processor.model.getEntity( fullID ) == None:
                if issubclass( type, viewobjs.SystemObject ):
                    if self.properties.has_key('DMClass'):
                        className = self.properties['DMClass']
                    else:
                        className = 'System'
                elif issubclass( type, viewobjs.VariableObject ):
                    if self.properties.has_key('DMClass'):
                        className = self.properties['DMClass']
                    else:
                        className = 'Variable'
                elif issubclass( type, viewobjs.ProcessObject ):
                    assert self.properties.has_key('DMClass')
                    className = self.properties['DMClass']
                runner.process( CreateEntity( className, fullID ) )
        return True

class DeleteViewObject( LayoutCommand ):
    __slots__ = [ 'id' ]

class ChangeViewObjectProperties( LayoutCommand ):
    __slots__ = [ 'id', 'properties' ]

class PasteLayoutBuffer( LayoutCommand ):
    __slots__ = [ 'parentID', 'buffer', 'modifiers' ]

class Commander( object ):
    def __init__( self, handler ):
        self.handler = handler

    def createEntity( self, className, fullID ):
        self.handler.process(
            CreateEntity( className = className, fullID = fullID ))

    def deleteEntity( self, fullID ):
        self.handler.process(
            DeleteEntity( fullID = fullID ))

    def changeEntityClass( self, fullID, newClassName ):
        self.handler.process(
            ChangeEntityClass(
                fullID = fullID, className = newClassName ))

    def changeEntityProperty( self, fullID, propertyName, newValue ):
        self.handler.process(
            ChangeEntityProperty(
                fullID = fullID, propertyName = propertyName,
                value = newValue ))

    def createEntityProperty( self, fullID, propertyName ):
        self.handler.process(
            CreateEntityProperty( 
                fullID = fullID, propertyName = propertyName ) )

    def deleteEntityProperty( self, fullID, propertyName ):
        self.handler.process(
            DeleteEntityProperty( 
                fullID = fullID, propertyName = propertyName ) )

    def renameEntityProperty( self, fullID, propertyName, newPropertyName ):
        self.handler.process(
            DeleteEntityProperty( 
                fullID = fullID, propertyName = propertyName,
                newPropertyName = newPropertyName ) )

    def setEntityInfo( self, fullID, info ):
        self.handler.process(
            SetEntityInfo(
                fullID = fullID, info = info ) )

    def moveEntity( self, fullID, newFullID ):
        self.handler.process(
            MoveEntity( 
                fullID = fullID, newFullID = newFullID ) )

    def addVariableReference( self, fullID, id, variableFullID, coef ):
        self.handler.process(
            AddVariableReference( 
                fullID = fullID, variableFullID = variableFullID,
                id = id, coefficient = coef ) )

    def deleteVariableReference( self, fullID, id ):
        self.handler.process(
            DeleteVariableReference( 
                fullID = fullID, id = id ) )

    def changeVariableReference( self, fullID, id, component, value ):
        self.handler.process(
            ChangeVariableReference(
                fullID = fullID, id = id,
                component = component, value = value ) )

    def createLayout( self, layoutID ):
        self.handler.process(
            CreateLayout( layoutID = layoutID ) )

    def deleteLayout( self, layoutID ):
        self.handler.process(
            DeleteLayout( layoutID = layoutID ) )

    def renameLayout( self, layoutID, newLayoutID ):
        self.handler.process(
            RenameLayout(
                layoutID = layoutID,
                newLayoutID = newLayoutID ) )

    def createViewObject( self, layoutID, id, type, **properties ):
        self.handler.process(
            CreateViewObject(
                layoutID = layoutID,
                id = id,
                type = type,
                properties = properties ) )

    def deleteViewObject( self, layoutID, id ):
        self.handler.process(
            DeleteViewObject( layoutID = layoutID, id = id ) )

    def pasteLayoutBuffer( self, layoutID, parentID, buffer, modifiers = None ):
        self.handler.process(
            PasteLayoutBuffer(
                layoutID = layoutID, 
                parentID = parentID, buffer = buffer,
                modifiers = modifiers ) )

    def moveViewObject( self, layoutID, id, x, y ):
        self.handler.process(
            ChangeViewObjectProperties(
                layoutID = layoutID,
                id = id,
                targets = { 'x': x, 'y': y } ) )

    def resizeViewObject( self, layoutID, id, width, height ):
        self.handler.process(
            ChangeViewObjectProperties(
                layoutID = layoutID,
                id = id, targets = { 'width': width, 'height': height } ) )

    def changeViewObjectProperties( self, layoutID, id, **properties ):
        self.handler.process(
            ChangeViewObjectProperties(
                layoutID = layoutID, id = id, targets = properties ) )
