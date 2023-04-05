\* context_map_prob *\
Minimize
OBJ: - crashme3:13_lb + crashme3:13_ub - crashme3:15_lb + crashme3:15_ub
 - crashme3:17_lb + crashme3:17_ub
Subject To
_C1: crashme3:13_lb - crashme3:13_ub <= 0
_C10: - crashme3:17_lb + crashme3:17_ub >= 4
_C11: crashme3:17_lb <= 11
_C12: crashme3:17_ub >= 15
_C2: crashme3:15_lb - crashme3:15_ub <= 0
_C3: crashme3:17_lb - crashme3:17_ub <= 0
_C4: - crashme3:13_lb + crashme3:13_ub >= 4
_C5: crashme3:13_lb <= 3
_C6: crashme3:13_ub >= 7
_C7: - crashme3:15_lb + crashme3:15_ub >= 4
_C8: crashme3:15_lb <= 7
_C9: crashme3:15_ub >= 11
Bounds
 crashme3:13_lb <= 15
 crashme3:13_ub <= 15
 crashme3:15_lb <= 15
 crashme3:15_ub <= 15
 crashme3:17_lb <= 15
 crashme3:17_ub <= 15
End
