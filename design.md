# Design

## Note

- 에전에 내가 생각한 방법은 seed 하나를 계속 update해 나가면서, FTI (GREYONE: Data Flow Sensitive Fuzzing, 2020)를 했을 때 얻어지는 data를 가지고 한다는 생각. 지금 다시 생각하다 보니까 더 general 하게 하는 걸 생각하게 되었는데, 그냥 fuzzing input이랑 각 input에 대한 coverage set 있을 때 거기서 decision tree를 만들어 내는.
- 어쨋든 전자의 방법이 더 좋은 건, 어떤 subset of input이 변화된 coverage에 영향을 주는지 안다는 것, 그리고 후자는 이걸 배워야한다는 점.
- 전자에서, static analysis로 dependence graph를 안다고 했을 때, branch condition point의 hierarchy도 안다고 했을 때, 위에서 부터 기준을 찾아가면 되는데
- 후자는 (지금의 간단한 implementation은) 이것부터 찾아가야 한단 말이지, 
- generate graph
  - 문제를 찾았네 지금은 일단 set이야 sequnece가 아니네 그러면 순서가 없네 generate tree from path가 안돼 path가 아니라서. path를 하는게 쉽나?

## Algorithm

### 전자
1. generate graph from coverage set
2. topological sort branches
3. for each branches
   1. identify set of inputs for each child
   2. generate predicate



