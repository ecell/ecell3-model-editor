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

from ecell.ui.model_editor.command import *
import ecell.ui.model_editor.command.executor as exe
import ecell.ui.model_editor.command.objects as cmds

class Journal:
    def __init__( self ):
        self.offset = 0
        self.entries = []

    def append( self, doItem, undoItem ):
        rev = len( self.entries ) + self.offset
        self.entries.append( { 'do': doItem, 'undo': undoItem } )
        return rev

    def __getitem__( self, rev ):
        return self.entries[ rev - self.offset ]

    def trash( self, uptoRev ):
        if uptoRev < self.offset:
            raise RuntimeError
        self.entries[ 0: uptoRev - self.offset + 1 ] = []
        self.offset = uptoRev

class TransactionError( RuntimeError ):
    pass

class TransactionRunner( object ):
    def __init__( self, executor, filter, journal ):
        self.executor = executor
        self.filter = filter
        self.journal = journal
        self.stack = []
        self.seq = None
        self.rseq = None

    def run( self, cmd ):
        self.seq = SequentialCommandGroup()
        self.rseq = ReversalCommandGroup()
        self.process( cmd )
        return self.journal.append( self.seq, self.rseq )

    def process( self, cmd ):
        self.seq.add( cmd )
        self.rseq.add( self.filter.filter( cmd ) )
        self.stack.append( ( self.seq, self.rseq ) )
        self.seq = SequentialCommandGroup()
        self.rseq = ReversalCommandGroup()
        if not cmd.prerequisite( self ):
            raise TransactionError, "Failed to fulfill the prerequisite of command \"%s\"" % cmd
        self.executor.process( cmd )
        seq, rseq = self.seq, self.rseq
        self.seq, self.rseq = self.stack.pop()
        self.seq.add( seq )
        self.rseq.add( rseq )

    def revert( self, rev ):
        entry = self.journal[ rev ]
        return self.run( entry[ 'undo' ] )

    def rerun( self, rev ):
        entry = self.journal[ rev ]
        return self.run( entry['do'] )

class Transaction( cmds.Commander ):
    def __init__( self, runner ):
        Commander.__init__( self, self )
        self.queue = cmds.SequentialCommandGroup()
        self.runner = runner
        self.committed = None

    def process( self, cmd ):
        self.queue.add( cmd )

    def commit( self ):
        if self.committed != None:
            raise TransactionError, "Transaction already committed"
        self.committed = self.runner.run( self.queue )

    def rollback( self ):
        if self.committed == None:
            raise TransactionError, "Transaction is not committed yet"
        self.runner.revert( self.committed )
        self.committed = None

