#!/usr/bin/env python
# -*- coding: utf-8 -*-

import vim
import joplin
import tree
import os
import sys
import re
from node import NoteNode

_treenodes = None
_show_help = False
_saved_pos = None
_j = None

_joplin_token = vim.vars.get('joplin_token', b'').decode()
_joplin_host = vim.vars.get('joplin_host', b'127.0.0.1').decode()
_joplin_port = int(vim.vars.get('joplin_port', b'41184').decode())
_joplin_window_width = int(vim.vars.get('joplin_window_width', b'30').decode())
_joplin_icon_open = vim.vars.get('joplin_icon_open', b'-').decode()
_joplin_icon_close = vim.vars.get('joplin_icon_close', b'+').decode()
_joplin_icon_todo = vim.vars.get('joplin_icon_todo', b'[ ]').decode()
_joplin_icon_completed = vim.vars.get('joplin_icon_completed', b'[x]').decode()
_joplin_icon_note = vim.vars.get('joplin_icon_note', b'').decode()

_window_title = [
    int((_joplin_window_width - 11) / 2) * '=' + ' Joplin ' + int(
        (_joplin_window_width - 11) / 2) * '=',
]

_help_lines = [
    '# Joplin quickhelp~',
    '# ' + (_joplin_window_width - 2) * '=',
    '# Note node mappings~',
    '# doublick-click: open in prev window',
    '# <CR>: open in prev window',
    '# o: open in prev window',
    '# t: open in new tab',
    '# i: open split',
    '# s: open vsplit',
    '# ',
    '# ' + (_joplin_window_width - 2) * '-',
    '# Notebook node mappings~',
    '# double-click: open & close node',
    '# <CR>: open & close node',
    '# o: open & close node',
    '# O: recursively open node',
    '# x: close parent of node',
    '# X: close all child nodes of current node recursively',
    '# ',
    '# ' + (_joplin_window_width - 2) * '-',
    '# Tree navigation mappings~',
    '# P: go to root',
    '# p: go to parent',
    '# K: go to first child',
    '# J: go to last child',
    '# <C-j>: go to next sibling',
    '# <C-k>: go to prev sibling',
    '# ',
    '# ' + (_joplin_window_width - 2) * '-',
    '# Other mappings~',
    '# q: Close the Joplin window',
    '# ?: toggle help',
    '',
]

props = {
    'joplin_folder': 'Identifier',
    'joplin_todo': 'Todo',
    'joplin_completed': 'Comment',
    'joplin_help_title': 'Define',
    'joplin_window_title': 'Constant',
    'joplin_help_keyword': 'Identifier',
    'joplin_help_summary': 'String',
    'joplin_help_sperate': 'String',
    'joplin_help_prefix': 'String',
}

for name, highlight in props.items():
    vim.Function('prop_type_add')(name, {'highlight': highlight})

_mapping_dict = {
    'o': 'cmd_o',
    '<cr>': 'cmd_o',
    '<2-LeftMouse>': 'cmd_o',
    't': 'cmd_t',
    'T': 'cmd_T',
    'i': 'cmd_i',
    's': 'cmd_s',
    'O': 'cmd_O',
    'x': 'cmd_x',
    'X': 'cmd_X',
    'P': 'cmd_P',
    'p': 'cmd_p',
    'K': 'cmd_K',
    'J': 'cmd_J',
    '<C-j>': 'cmd_ctrl_j',
    '<C-k>': 'cmd_ctrl_k',
    'q': 'cmd_q',
    '?': 'cmd_question_mark',
}

_unmap = [
    'r', 'R', '<C-r>', 'u', 'U', 'I', 'a', 'A', 's', 'S', 'd', 'D', 'c', 'C'
]


def get_joplin():
    global _j
    if _j is None:
        token = vim.vars.get('joplin_token', b'').decode()
        host = vim.vars.get('joplin_host', b'127.0.0.1').decode()
        port = int(vim.vars.get('joplin_port', b'41184').decode())
        if token == '':
            print('Joplin: g:joplin_token is empty')
            sys.exit(-1)

        _j = joplin.Joplin(token, host, port)
        if _j is None:
            print('Joplin: can not create joplin instance')
            sys.exit(-1)
    return _j


def open_window():
    """open joplin window
    """
    bufname_ = bufname()
    winnr = vim.eval('bufwinnr("%s")' % bufname_)
    winnr = int(winnr)
    if winnr != -1:
        vim.command('win_gotoid("%s")' % winnr)
        return
    vim.command('silent keepalt topleft vertical %d split %s' %
                (_joplin_window_width, bufname_))
    set_options()
    set_map()
    render()


def close_window():
    bufname_ = bufname()
    winnr = vim.Function('bufwinnr')(bufname_)
    if winnr > 0:
        vim.command('%dclose' % winnr)


def write():
    joplin_note_id = get_editting_note_id()
    if joplin_note_id == '':
        return

    note = get_joplin().get(NoteNode, joplin_note_id)
    if note is None:
        return

    note.body = '\n'.join(vim.current.buffer[:])
    get_joplin().put(note)


def set_options():
    vim.current.buffer.options['bufhidden'] = 'hide'
    vim.current.buffer.options['buftype'] = 'nofile'
    vim.current.buffer.options['swapfile'] = False
    vim.current.buffer.options['filetype'] = 'joplin'
    vim.current.buffer.options['modifiable'] = False
    vim.current.buffer.options['readonly'] = False
    vim.current.buffer.options['buflisted'] = False
    vim.current.buffer.options['textwidth'] = 0
    vim.current.window.options['signcolumn'] = 'no'
    vim.current.window.options['winfixwidth'] = True
    vim.current.window.options['foldcolumn'] = 0
    vim.current.window.options['foldmethod'] = 'manual'
    vim.current.window.options['foldenable'] = False
    vim.current.window.options['list'] = False
    vim.current.window.options['spell'] = False
    vim.current.window.options['wrap'] = False
    vim.current.window.options['number'] = True
    vim.current.window.options['relativenumber'] = False
    vim.current.window.options['cursorline'] = True


def set_map():
    for lhs in _unmap:
        cmd = 'nnoremap <script><silent><buffer>%s <nop>' % lhs
        vim.command(cmd)
    for lhs, rhs in _mapping_dict.items():
        cmd = 'nnoremap <script><silent><buffer>%s <esc>:<c-u>pythonx jplvim.%s()<cr>' % (
            lhs, rhs)
        vim.command(cmd)


def bufname():
    return 'tree.joplin'


def help_len():
    return len(_help_lines) if has_help() else 0


def base_line():
    return len(_window_title) + (len(_help_lines) if has_help() else 0)


def prop_add(nr, prop_type, col_begin=1, col_end=0):
    if prop_type == '':
        return
    vim.Function('cursor')(nr, 1)
    if col_end == 0:
        col_end = vim.Function('col')('$')
    vim.Function('prop_add')(nr, col_begin, {
        'end_col': col_end,
        'type': prop_type,
    })


def render_help(nr):
    help_lines = _help_lines if has_help() else []
    for text in help_lines:
        vim.current.buffer.append(text, nr)
        prop_add(nr + 1, 'joplin_help_prefix', 1, 3)
        if re.match(r'^# =+$|^# -+$', text):
            prop_add(nr + 1, 'joplin_help_sperate', 3)
        elif re.match(r'^# .*~$', text):
            prop_add(nr + 1, 'joplin_help_title', 3)
        elif re.match(r'^# [^:]*:.*$', text):
            vim.Function('cursor')(nr + 1, 1)
            vim.command('noautocmd normal f:')
            col = vim.Function('col')('.')
            prop_add(nr + 1, 'joplin_help_keyword', 3, col)
            prop_add(nr + 1, 'joplin_help_summary', col)
        nr += 1
    return nr


def render_title(nr):
    for text in _window_title:
        vim.current.buffer.append(text, nr)
        prop_add(nr + 1, 'joplin_window_title')
        nr += 1
    return nr


def render_nodes(nr):
    global _treenodes
    if _treenodes is None:
        _treenodes = tree.construct_folder_tree(get_joplin())
    lines = note_text(_treenodes, 0)
    for line in lines:
        vim.current.buffer.append(
            line.text(_joplin_icon_open, _joplin_icon_close, _joplin_icon_note,
                      _joplin_icon_todo, _joplin_icon_completed), nr)
        line.lineno = nr + 1
        prop_type = line.prop_type()
        prop_add(nr + 1, prop_type)
        nr += 1
    return nr


def render():
    vim.current.buffer.options['modifiable'] = True
    del vim.current.buffer[:]
    nr = 0
    nr = render_help(nr)
    nr = render_title(nr)
    nr = render_nodes(nr)
    # delete empty line
    del vim.current.buffer[nr]
    vim.current.buffer.options['modifiable'] = False


def note_text(nodes, indent):
    lines = []
    for node in nodes:
        node.indent = indent
        lines.append(node)
        if node.is_open():
            sub = note_text(node.children, indent + 1)
            lines += sub
    return lines


def has_help():
    return vim.current.buffer.vars.get('joplin_help', False)


def get_cur_line():
    lineno = int(vim.eval('line(".")'))
    if lineno <= base_line():
        return None
    return find_treenode(_treenodes, lineno)


def find_treenode(nodes, lineno):
    i = 0
    j = len(nodes) - 1

    if i > j:
        return None
    if nodes[j].lineno < lineno:
        return find_treenode(nodes[j].children,
                             lineno) if nodes[j].is_folder() else None
    while i <= j:
        mid = int((i + j) / 2)
        if nodes[mid].lineno == lineno:
            return nodes[mid]
        elif nodes[mid].lineno < lineno:
            i = mid + 1
        elif nodes[mid].lineno > lineno:
            j = mid - 1

    mid = i if nodes[i].lineno < lineno else i - 1
    return find_treenode(nodes[mid].children,
                         lineno) if nodes[mid].is_folder() else None


def get_editting_note_id():
    joplin_note_id = vim.current.buffer.vars.get('joplin_note_id',
                                                 b'').decode()
    return joplin_note_id


def set_editting_note_id(id):
    vim.current.buffer.vars['joplin_note_id'] = id


def edit(command, treenode):
    lazyredraw_saved = vim.options['lazyredraw']
    dirname = vim.eval('tempname()')
    os.mkdir(dirname)
    filename = dirname + '/' + treenode.node.title + '.md'
    vim.command('silent %s %s' % (command, filename))
    set_editting_note_id(treenode.node.id)
    treenode.fetch(get_joplin())
    vim.current.buffer[:] = treenode.node.body.split('\n')
    vim.command('silent noautocmd w')
    vim.options['lazyredraw'] = lazyredraw_saved
    vim.command('autocmd BufWritePost <buffer> pythonx jplvim.write()')


def go_to_previous_win():
    saved_winnr = vim.current.buffer.vars.get('saved_winnr', -1)
    if saved_winnr > 0:
        vim.command('%dwincmd w' % saved_winnr)
    else:
        vim.command('wincmd w')


def cursor(treenode):
    if treenode.lineno > 0:
        vim.Function('cursor')(treenode.lineno, 1)


def cmd_o():
    treenode = get_cur_line()
    if treenode is None:
        return
    if treenode.is_folder():
        if treenode.is_open():
            treenode.close()
        else:
            treenode.open(get_joplin())
        saved_pos = vim.eval('getcurpos()')
        render()
        vim.Function('setpos')('.', saved_pos)
    else:
        go_to_previous_win()
        edit('edit', treenode)


def cmd_t():
    treenode = get_cur_line()
    if treenode is None:
        return

    if treenode.is_folder():
        edit('tabnew', treenode)


def cmd_i():
    treenode = get_cur_line()
    if treenode is None:
        return
    if not treenode.is_folder():
        go_to_previous_win()
        edit('split', treenode)


def cmd_s():
    treenode = get_cur_line()
    if treenode is None:
        return
    if not treenode.is_folder():
        go_to_previous_win()
        edit('vsplit', treenode)


def open_recusively(treenode):
    if treenode.is_folder() and not treenode.is_open():
        treenode.open(get_joplin())

    for child in treenode.children:
        open_recusively(child)


def cmd_O():
    treenode = get_cur_line()
    if treenode is None:
        return
    if treenode.is_folder():
        open_recusively(treenode)
        render()
        cursor(treenode)


def cmd_x():
    treenode = get_cur_line()
    if treenode is None:
        return
    treenode = treenode if \
        treenode.is_folder() and treenode.is_open() else \
        treenode.parent
    while treenode is not None and not treenode.is_folder():
        treenode = treenode.parent

    if treenode is not None:
        treenode.close()
        render()
        cursor(treenode)


def close_recurisive(node):
    if not node.is_folder() or not node.is_open():
        return

    node.close()
    for child in node.children:
        close_recurisive(child)


def cmd_X():
    treenode = get_cur_line()
    if not treenode.is_folder():
        return
    close_recurisive(treenode)
    render()
    cursor(treenode)


def cmd_P():
    treenode = get_cur_line()
    if treenode is None:
        return
    while treenode.parent is not None:
        treenode = treenode.parent
    cursor(treenode)


def cmd_p():
    treenode = get_cur_line()
    if treenode is None:
        return
    treenode = treenode.parent if treenode.parent is not None else treenode
    cursor(treenode)


def cmd_K():
    treenode = get_cur_line()
    if treenode is None:
        return
    nodes = treenode.parent.children if \
        treenode.parent is not None else \
        _treenodes
    if len(nodes) > 0:
        cursor(nodes[0])


def cmd_J():
    treenode = get_cur_line()
    if treenode is None:
        return
    nodes = treenode.parent.children if \
        treenode.parent is not None else \
        _treenodes
    if len(nodes) > 0:
        cursor(nodes[-1])


def cmd_ctrl_j():
    treenode = get_cur_line()
    if treenode is None:
        return
    nodes = treenode.parent.children if \
        treenode.parent is not None else \
        _treenodes
    i = treenode.child_index_of_parent + 1
    if i < len(nodes):
        cursor(nodes[i])


def cmd_ctrl_k():
    treenode = get_cur_line()
    if treenode is None:
        return
    nodes = treenode.parent.children if \
        treenode.parent is not None else \
        _treenodes
    i = treenode.child_index_of_parent - 1
    if i >= 0:
        cursor(nodes[i])


def cmd_q():
    close_window()


def cmd_question_mark():
    joplin_help = has_help()
    vim.current.buffer.vars['joplin_help'] = not joplin_help
    render()
    vim.Function('cursor')(1, 1)
