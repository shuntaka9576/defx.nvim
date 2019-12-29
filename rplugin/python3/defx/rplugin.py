# ============================================================================
# FILE: rplugin.py
# AUTHOR: Shougo Matsushita <Shougo.Matsu at gmail.com>
# License: MIT license
# ============================================================================

import typing
from logging import getLogger

from defx.clipboard import Clipboard
from defx.view import View
from defx.util import Nvim

logger = getLogger(__name__)
debug = logger.debug


class Rplugin:

    def __init__(self, vim: Nvim) -> None:
        self._vim = vim
        self._views: typing.List[View] = []
        self._clipboard = Clipboard()

    def init_channel(self) -> None:
        self._vim.vars['defx#_channel_id'] = self._vim.channel_id

    def start(self, args: typing.List[typing.Any]) -> None:
        [paths, context] = args

        debug("paths: %s", paths)
        debug("context: %s", context)

        views = [x for x in self._views
                 if context['buffer_name'] == x._context.buffer_name]
        debug("views: %s", views)  # 初回起動時は空っぽ
        debug("context[new]: %s", context['new'])  # 初回起動時はFlase
        if not views or context['new']:
            debug("[before]self._views: %s", self._views)
            view = View(self._vim, len(self._views))
            debug("view: %s", view)
            views = [view]
            self._views.append(view)
        debug("[after]self._views: %s", self._views)
        views[0].init(paths, context, self._clipboard)  # 冗長さ意図

    def do_action(self, args: typing.List[typing.Any]) -> None:
        views = [x for x in self._views
                 if x._bufnr == self._vim.current.buffer.number]
        if not views:
            return
        view = views[0]

        prev_paths = [x._cwd for x in view._defxs]
        prev_candidates = view._candidates

        view.do_action(args[0], args[1], args[2])

        paths = [x._cwd for x in view._defxs]
        if paths == prev_paths and view._candidates != prev_candidates:
            self.redraw([x for x in self._views if x != view])

    def get_candidate(self) -> typing.Dict[str, typing.Union[str, bool]]:
        cursor = self._vim.call('line', '.')
        for view in [x for x in self._views
                     if x._bufnr == self._vim.current.buffer.number]:
            candidate = view.get_cursor_candidate(cursor)
            return {
                'word': candidate['word'],
                'is_directory': candidate['is_directory'],
                'is_opened_tree': candidate['is_opened_tree'],
                'level': candidate['level'],
                'action__path': str(candidate['action__path']),
            }
        return {}

    def get_context(self) -> typing.Dict[str, typing.Any]:
        for view in [x for x in self._views
                     if x._bufnr == self._vim.current.buffer.number]:
            return view._context._asdict()
        return {}

    def redraw(self, views: typing.List[View]) -> None:
        call = self._vim.call
        for view in [x for x in views
                     if call('bufwinnr', x._bufnr) > 0]:
            view.redraw(True)
