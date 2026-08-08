import VeyraNativeSemantics

/- Strict fixed-anchor unary runtime mirrored by src/core/intrinsic_arithmetic.py. -/
namespace VeyraIntrinsicRuntime

def originNode : VeyraNod := node "intrinsic-origin"

def successorTact : VeyraTact :=
  { start := originNode, stop := originNode, mark := "intrinsic-successor" }

def canonicalBreath (run : List VeyraTact) : VeyraBreath :=
  match run with
  | [] => { tacts := [], anchor := some originNode }
  | _ :: _ => { tacts := run, anchor := none }

def canonicalTacts : List VeyraTact → Bool
  | [] => true
  | head :: tail => decide (head = successorTact) && canonicalTacts tail

def canonicalMode (value : VeyraMode) : Bool :=
  decide (value.observer = "native-cycle") &&
    match value.breath.tacts, value.breath.anchor with
    | [], some anchor => decide (anchor = originNode)
    | [], none => false
    | _ :: _, some _ => false
    | run, none => canonicalTacts run

def zero : VeyraMode :=
  { breath := canonicalBreath [], observer := "native-cycle" }

def successor (value : VeyraMode) : VeyraResult VeyraMode :=
  if canonicalMode value then
    .ready {
      breath := canonicalBreath (successorTact :: value.breath.tacts)
      observer := "native-cycle"
    }
  else .blocked "foreign-recurrence"

def stitch (left right : VeyraMode) : VeyraResult VeyraMode :=
  if canonicalMode left && canonicalMode right then
    .ready {
      breath := canonicalBreath (left.breath.tacts ++ right.breath.tacts)
      observer := "native-cycle"
    }
  else .blocked "foreign-recurrence"

def repeatTacts (run : List VeyraTact) : List VeyraTact → List VeyraTact
  | [] => []
  | _ :: tail => run ++ repeatTacts run tail

def weave (left right : VeyraMode) : VeyraResult VeyraMode :=
  if canonicalMode left && canonicalMode right then
    .ready {
      breath := canonicalBreath (repeatTacts left.breath.tacts right.breath.tacts)
      observer := "native-cycle"
    }
  else .blocked "foreign-recurrence"

end VeyraIntrinsicRuntime
