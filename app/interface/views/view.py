import tkinter as tk
from tkinter import ttk

class View:

    def __init__(self, parent):
        self.frame = ttk.Frame(parent)

    def init(self):
        raise NotImplementedError('This method should be overridden by child')