from pyrser import meta, directives
from pyrser.grammar import Grammar
from pyrser.hooks import copy, echo
from pyrser.parsing.node import Node
from pyrser.directives import ignore
from cnorm import nodes
from cnorm.parsing.expression import Expression

class Statement(Grammar, Expression):
    """
        interaction with other CNORM PART:

        Declaration.init_declarator -> compound_statement
        Expression.primary_expression -> block_item_list
    """
    entry = "single_statement"
    grammar = """

        /*
            Comment works as in C/C++
        */

        single_statement ::=
            compound_statement:_
            | labeled_statement:_
            | expression_statement:_
        ;

        compound_statement ::=
            [
            '{' 
                "":current_block
                #new_blockstmt(_, current_block)
                [
                    line_of_code
                ]*
            '}'
            ]
        ;

        line_of_code ::=
            single_statement:line
            #end_loc(current_block, line)
        ;

        labeled_statement ::=
            rootidentifier:id
            [
            #check_stmt(id, "if") if_statement:_
            | #check_stmt(id, "for") for_statement:_
            | #check_stmt(id, "while") while_statement:_
            | #check_stmt(id, "switch") switch_statement:_
            | #check_stmt(id, "do") do_statement:_
            | #check_stmt(id, "return") return_statement:_
            | #check_stmt(id, "goto") goto_statement:_
            | #check_stmt(id, "case") case_statement:_
            | #check_stmt(id, "break") ';' #new_break(_)
            | #check_stmt(id, "continue") ';' #new_continue(_)
            | ':' #new_label(_, id)
            ]
        ;

        if_statement ::=
            '(' expression:cond ')'
            single_statement:then
            ["else"
            // TODO: explain variable forwarding of 'else'
            single_statement:else 
            ]?:else
            #new_if(_, cond, then, else)
        ;

        for_statement ::=
            '(' // TODO: optionals
                expression:init ';'
                expression:cond ';'
                expression:inc
            ')'
            single_statement:body
            #new_for(_, init, cond, inc, body)
        ;

        while_statement ::=
            '(' expression:cond ')'
            single_statement:body
            #new_while(_, cond, body)
        ;

        switch_statement ::=
            '(' expression:cond ')'
            single_statement:body
            #new_switch(_, cond, body)
        ;

        do_statement ::=
            single_statement:body
            "while" '(' expression:cond ')' ';'
            #new_do(_, cond, body)
        ;

        return_statement ::=
            [expression:e ]?:e ';'
            #new_return(_, e)
        ;

        goto_statement ::=
            expression:e ';'
            #new_goto(_, e)
        ;

        case_statement ::=
            [expression:e ]?:e ':'
            #new_case(_, e)
        ;

        expression_statement ::=
            [expression:e #new_expr(_, e) ]? ';'
        ;

    """

    def parse(self, source, entry=None):
        res = Grammar.parse(self, source, entry)
        if hasattr(res, 'node'):
            return res.node
        return res

@meta.hook(Statement)
def new_expr(self, ast, expr):
    ast.node = nodes.ExprStmt(expr.node)
    return True

@meta.hook(Statement)
def new_if(self, ast, cond_expr, then_expr, else_expr):
    thenbody = None
    if hasattr(then_expr, 'node'):
        thenbody = then_expr.node
    if hasattr(else_expr, 'node'):
        ast.node = nodes.If(cond_expr.node, thenbody, else_expr.node)
    else:
        ast.node = nodes.If(cond_expr.node, thenbody)
    return True

@meta.hook(Statement)
def new_for(self, ast, init, cond, inc, body):
    ast.node = nodes.For(init.node, cond.node, inc.node, body.node)
    return True

@meta.hook(Statement)
def new_while(self, ast, cond, body):
    thebody = None
    if hasattr(body, 'node'):
        thebody = body.node
    ast.node = nodes.While(cond.node, thebody)
    return True

@meta.hook(Statement)
def new_switch(self, ast, cond, body):
    thebody = None
    if hasattr(body, 'node'):
        thebody = body.node
    ast.node = nodes.Switch(cond.node, thebody)
    return True

@meta.hook(Statement)
def new_do(self, ast, cond, body):
    thebody = None
    if hasattr(body, 'node'):
        thebody = body.node
    ast.node = nodes.Do(cond.node, thebody)
    return True

@meta.hook(Statement)
def new_return(self, ast, expr):
    theexpr = None
    if hasattr(expr, 'node'):
        theexpr = expr.node
    ast.node = nodes.Return(theexpr)
    return True

@meta.hook(Statement)
def new_goto(self, ast, expr):
    ast.node = nodes.Goto(expr.node)
    return True

@meta.hook(Statement)
def new_case(self, ast, expr):
    ast.node = nodes.Case(expr.node)
    return True

@meta.hook(Statement)
def new_break(self, ast):
    ast.node = nodes.Break()
    return True

@meta.hook(Statement)
def new_continue(self, ast):
    ast.node = nodes.Continue()
    return True

@meta.hook(Statement)
def new_label(self, ast, ident):
    ast.node = nodes.Label(ident.value)
    return True

@meta.hook(Statement)
def new_blockstmt(self, ast, current_block):
    ast.node = nodes.BlockStmt([])
    current_block.node = ast.node
    parent = self.rulenodes.parents
    if 'current_block' in parent:
        current_block.node.types = parent['current_block'].node.types.new_child()
    return True

@meta.hook(Statement)
def end_loc(self, current_block, ast):
    line = None
    if hasattr(ast, 'node'):
        line = ast.node
    current_block.node.body.append(line)
    return True

@meta.hook(Statement)
def check_stmt(self, ident, val):
    return ident.value == val
