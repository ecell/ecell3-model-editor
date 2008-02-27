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

import ecell.ecs_constants as econsts
from ecell.DMInfo import DMPropertyDescriptor
from ecell.ui.model_editor.command import *
import ecell.ui.model_editor.command.objects as cmds

class ReverseCommandFilter( object, CommandFilter ):
    def __init__( self, model, layout ):
        self.model = model
        self.layout = layout

    def filter( self, cmd ):
        if isinstance( cmd, AtomicCommand ):
            mtd = cmd.__class__.__name__
            mtd = '_' + self.__class__.__name__ + '__' + mtd[ 0 ].lower() + mtd[ 1: ]
            return getattr( self, mtd )( **cmd.operands )
        elif isinstance( cmd.__class__, CommandGroup ):
            queue = ReversalCommandGroup()
            for subCmd in cmd.commands:
                queue.append( self.filter( subCmd ) )
            return queue

    def __createEntity( self, className, fullID ):
        return cmds.DeleteEntity( fullID = fullID )

    def __deleteEntity( self, fullID ):
        entity = self.model.getEntity( fullID )
        group = SequentialCommandGroup()
        group.add(
            cmds.CreateEntity(
                fullID = fullID, className = entity.klass.name )
            )
        for propName, slot in entity.getPropertySlots().iteritems():
            if slot.descriptor.isSettable and slot.descriptor.isGettable:
                group.add(
                    cmds.ChangeEntityProperty(
                        fullID = fullID, propertyName = propName,
                        value = slot.value ) )
        return group

    def __changeEntityClass( self, fullID, newClassName ):
        entity = self.model.getEntity( fullID )
        return cmds.ChangeEntityClass(
            fullID = fullID, className = entity.klass.name )

    def __changeEntityProperty( self, fullID, propertyName, newValue ):
        oldValue = self.model.getEntity( fullID ).getProperty( propertyName )
        return cmds.ChangeEntityProperty(
            fullID = fullID, propertyName = propertyName,
            value = oldValue )

    def __createEntityProperty( self, fullID, propertyName ):
        return cmds.DeleteEntityProperty(
            fullID = fullID, propertyName = propertyName )

    def __deleteEntityProperty( self, fullID, propertyName ):
        oldValue = self.model.getEntity( fullID ).getProperty( propertyName )
        group = SequentialCommandGroup()
        group.add(
            cmds.CreateEntityProperty(
                fullID = fullID, propertyName = PropertyName )
            )
        group.add(
            cmds.ChangeEntityProperty(
                fullID = fullID, propertyName = propertyName,
                value = oldValue ) )
        return group

    def __renameEntityProperty( self, fullID, propertyName, newPropertyName ):
        return cmds.RenameEntityProperty(
            fullID = fullID, propertyName = newPropertyName,
            newPropertyName = propertyName )

    def __setEntityInfo( self, fullID, info ):
        oldValue = self.model.getEntity( fullID ).getAnnotation( 'info' )
        return cmds.SetEntityInfo( fullID = fullID, info = oldValue )

    def __moveEntity( self, fullID, newFullID ):
        return cmds.MoveEntity( fullID = newFullID, newFullID = fullID )

    def __addVariableReference( self, fullID, id, variableFullID, coefficient ):
        return cmds.DeleteVariableReference( fullID = fullID, id = id )

    def __deleteVariableReference( self, fullID, id ):
        proc = self.model.getEntity( fullID )
        rel = proc.getVariableReference( id )
        return cmds.AddVariableReference(
            fullID = fullID, 
            id = id,
            variableFullID = self.model.fullIDOf(
                rel.counterpartOf( proc ) ),
            coefficient = rel.coefficient
            )

    def __changeVariableReference( self, fullID, id, component, value ):
        proc = self.model.getEntity( fullID )
        rel = proc.getVariableReference( id )
        oldValue = getattr( rel, component )
        return cmds.ChangeVariableReference(
            fullID = fullID, id = id,
            component = component, value = oldValue )

class CommandExecutor( object, CommandProcessor ):
    def __init__( self, model, layout ):
        self.model = model
        self.layout = layout
        self.stack = []

    def dispatch( self, cmd ): 
        mtd = cmd.__class__.__name__
        mtd = '_' + self.__class__.__name__ + '__' + mtd[ 0 ].lower() + mtd[ 1: ]
        getattr( self, mtd )( **cmd.operands )

    def process( self, cmd ):
        if isinstance( cmd, AtomicCommand ):
            self.dispatch( cmd )
        elif isinstance( cmd, CommandGroup ):
            for _cmd in cmd.commands:
                assert _cmd != cmd
                self.process( _cmd )

    def __createEntity( self, className, fullID ):
        self.model.createEntity( className, fullID )

    def __deleteEntity( self, fullID ):
        self.model.deleteEntity( fullID )

    def __changeEntityClass( self, fullID, newClassName ):
        self.model.changeEntityClass( fullID, newClassName )

    def __changeEntityProperty( self, fullID, propertyName, newValue ):
        self.model.getEntity( self.fullID ).setProperty( propertyName, value )

    def __createEntityProperty( self, fullID, propertyName ):
        desc = DMPropertyDescriptor(
            typeCode   = econsts.DM_PROP_TYPE_POLYMORPH,
            attributes = econsts.DM_PROP_ATTR_SETTABLE \
                | econsts.DM_PROP_ATTR_GETTABLE \
                | econsts.DM_PROP_ATTR_LOADABLE \
                | econsts.DM_PROP_ATTR_SAVEABLE,
            defaultValue = '' )
        slot = self.model.getEntity( self, fullID ).addPropertySlot(
            propertyName, desc )
        pass

    def __deleteEntityProperty( self, fullID, propertyName ):
        self.model.getEntity( self.fullID ).removePropertySlot( propertyName )

    def __renameEntityProperty( self, fullID, propertyName, newPropertyName ):
        ent = self.model.getEntity( self.fullID )
        slot = ent.getPropertySlot( propertyName )
        ent.removePropertySlot( propertyName )
        newSlot = ent.addPropertySlot( newPropertyName, slot.desc )
        newSlot.value = slot.value

    def __setEntityInfo( self, fullID, info ):
        ent = self.model.getEntity( fullID )
        ent.setAnnotation( 'info', info )

    def __moveEntity( self, fullID, newFullID ):
        self.model.moveEntity( fullID, newFullID )

    def __addVariableReference( self, fullID, id, variableFullID, coefficient ):
        proc = self.model.getEntity( fullID )
        proc.addVariableReference(
            self.model.getEntity( variableFullID ),
            coefficient, id )

    def __deleteVariableReference( self, fullID, id ):
        proc = self.model.getEntity( fullID )
        proc.removeVariableReference(
            self.model.getEntity( variableFullID ), id )

    def __changeVariableReference( self, fullID, id, component, value ):
        proc = self.model.getEntity( fullID )
        rel = proc.variableReferences[ id ]
        proc.removeVariableReference( id )
        setattr( rel, component, value )
        proc.addVariableReference(
            rel.counterpartOf( proc ), rel.coefficient, rel.name )


