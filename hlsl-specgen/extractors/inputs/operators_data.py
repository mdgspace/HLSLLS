OPERATORS = [
    # Postfix / primary
    { "name": "()",   "precedence": 1,  "left_to_right": True,  "kind": "postfix" },  # function call
    { "name": "[]",   "precedence": 1,  "left_to_right": True,  "kind": "postfix" },  # indexing
    { "name": ".",    "precedence": 1,  "left_to_right": True,  "kind": "infix"   },  # member/swizzle
    { "name": "++",   "precedence": 1,  "left_to_right": True,  "kind": "postfix" },
    { "name": "--",   "precedence": 1,  "left_to_right": True,  "kind": "postfix" },

    # Prefix / unary
    { "name": "++",   "precedence": 2,  "left_to_right": False, "kind": "prefix"  },
    { "name": "--",   "precedence": 2,  "left_to_right": False, "kind": "prefix"  },
    { "name": "+",    "precedence": 2,  "left_to_right": False, "kind": "prefix"  },  # unary plus
    { "name": "-",    "precedence": 2,  "left_to_right": False, "kind": "prefix"  },  # unary minus
    { "name": "!",    "precedence": 2,  "left_to_right": False, "kind": "prefix"  },  # logical NOT
    { "name": "~",    "precedence": 2,  "left_to_right": False, "kind": "prefix"  },  # bitwise NOT
    { "name": "(type)", "precedence": 2,  "left_to_right": False, "kind": "prefix"  },  # (type)expr

    # Multiplicative
    { "name": "*",    "precedence": 3,  "left_to_right": True,  "kind": "infix"   },
    { "name": "/",    "precedence": 3,  "left_to_right": True,  "kind": "infix"   },
    { "name": "%",    "precedence": 3,  "left_to_right": True,  "kind": "infix"   },

    # Additive
    { "name": "+",    "precedence": 4,  "left_to_right": True,  "kind": "infix"   },
    { "name": "-",    "precedence": 4,  "left_to_right": True,  "kind": "infix"   },

    # Shift
    { "name": "<<",   "precedence": 5,  "left_to_right": True,  "kind": "infix"   },
    { "name": ">>",   "precedence": 5,  "left_to_right": True,  "kind": "infix"   },

    # Relational
    { "name": "<",    "precedence": 6,  "left_to_right": True,  "kind": "infix"   },
    { "name": "<=",   "precedence": 6,  "left_to_right": True,  "kind": "infix"   },
    { "name": ">",    "precedence": 6,  "left_to_right": True,  "kind": "infix"   },
    { "name": ">=",   "precedence": 6,  "left_to_right": True,  "kind": "infix"   },

    # Equality
    { "name": "==",   "precedence": 7,  "left_to_right": True,  "kind": "infix"   },
    { "name": "!=",   "precedence": 7,  "left_to_right": True,  "kind": "infix"   },

    # Bitwise
    { "name": "&",    "precedence": 8,  "left_to_right": True,  "kind": "infix"   },
    { "name": "^",    "precedence": 9,  "left_to_right": True,  "kind": "infix"   },
    { "name": "|",    "precedence": 10, "left_to_right": True,  "kind": "infix"   },

    # Logical
    { "name": "&&",   "precedence": 11, "left_to_right": True,  "kind": "infix"   },
    { "name": "||",   "precedence": 12, "left_to_right": True,  "kind": "infix"   },

    # Ternary conditional
    { "name": "?",   "precedence": 13, "left_to_right": False, "kind": "infix" },
    { "name": ":",   "precedence": 13, "left_to_right": False, "kind": "infix" },

    # Assignment
    { "name": "=",    "precedence": 14, "left_to_right": False, "kind": "infix"   },
    { "name": "+=",   "precedence": 14, "left_to_right": False, "kind": "infix"   },
    { "name": "-=",   "precedence": 14, "left_to_right": False, "kind": "infix"   },
    { "name": "*=",   "precedence": 14, "left_to_right": False, "kind": "infix"   },
    { "name": "/=",   "precedence": 14, "left_to_right": False, "kind": "infix"   },
    { "name": "%=",   "precedence": 14, "left_to_right": False, "kind": "infix"   },
    { "name": "<<=",  "precedence": 14, "left_to_right": False, "kind": "infix"   },
    { "name": ">>=",  "precedence": 14, "left_to_right": False, "kind": "infix"   },
    { "name": "&=",   "precedence": 14, "left_to_right": False, "kind": "infix"   },
    { "name": "^=",   "precedence": 14, "left_to_right": False, "kind": "infix"   },
    { "name": "|=",   "precedence": 14, "left_to_right": False, "kind": "infix"   },

    # Comma
    { "name": ",",    "precedence": 15, "left_to_right": True,  "kind": "infix"   }
]
