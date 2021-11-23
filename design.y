%token Bool
%token Int
%token Input
%token LineNo
%token FuncName

%%

Inputs
    : %empty
    | Input ';' Inputs

CallContext
    : %empty
    | '(' FuncName LineNo ')'

CallStack
    : %empty
    | CallContext ';' CallStack

Coverage: '(' FuncName LineNo ')'

Branch: '(' FuncName LineNo ')'

ContCov: '(' CallStack Coverage ')'


Path
    : %empty
    | ContCov ';' Path

Record
    : %empty
    | '(' Path ':' Inputs ')' ';' Record

Edge: '(' Coverage Coverage ')'

MapFunc_: Int '>' Int

Ints
    : %empty
    | Int ';' Ints

Pred_: Ints '>' Bool

EdgeCond
    : %empty
    | '(' Edge ':' Pred_ ')' ';' EdgeCond

ContextMap
    : %empty
    | '(' CallContext ':' MapFunc_ ')' ';' ContextMap


CFM: '(' EdgeCond ContextMap ')'

Coverages
    : %empty
    | Coverage ';' Coverages

BranchMap_ : Branch '>' ContCov

CoverageTrees
    : %empty
    | '(' Coverage ':' Coverages ')' ';' CoverageTrees

%%