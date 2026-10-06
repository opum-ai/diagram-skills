# Pitching a diagram and its explanation to the reader

A diagram never ships alone. It answers one question, stated in the
sentence before it, and a plain-English explanation follows it. The
explanation is also the diagram's long description for screen-reader users
(WCAG 1.1.1), so a reader who cannot see the picture still gets the
answer.

The levels follow the plain-english-styles output styles. Pick the level in
this order:

1. the level the user names ("explain it to a non-engineer");
2. the active output style, if it is `plain-english-beginner`,
   `plain-english-intermediate` or `plain-english-advanced`;
3. otherwise **intermediate**.

## The three levels

| | Beginner | Intermediate | Advanced |
|---|---|---|---|
| Reader | Smart, does not write code | Product owner; knows the product, not the internals | Staff engineer |
| Diagrams per answer | At most one, and only if the answer has a shape | One | Several, if each answers a different question |
| Node cap | **7** | **12** | **20**, then split |
| Labels | Plain words. No ids, file names, acronyms or jargon | Real names, glossed on first use | Ids, technologies, precise terms |
| Structure | `flowchart LR`, no subgraphs, at most one highlight | One level of grouping; a verb on every edge; a legend if colour or line style means anything | Subgraphs, several edge kinds, critical path |
| Explanation | Conclusion first; then one line per box that is not obvious | What it shows and how we know; then the one thing to act on | The claim, the mechanism, the action. May be shorter than the diagram |

The caps come from the research, not taste. Working memory holds about four
chunks. Node-link diagrams get hard to read past about 20 nodes. Practitioner
caps sit between 12 and 20. Above the cap, split the picture by question; do
not shrink the font.

## The shape of an answer

~~~text
<One sentence: the question this diagram answers, or the claim it makes.>

```mermaid
...
```

<Explanation: read the diagram in words, at the reader's level.>
~~~

The lint checks that both are present. The explanation needs at least 20
words after the fence.

### Beginner example

> The new checkout waits for payment before it ships anything.
>
> *(diagram: four boxes, Order placed → Payment checked → Packed → Shipped)*
>
> Read it left to right. Nothing is packed until the payment check passes,
> so a failed card never turns into a parcel. "Payment checked" is the step
> that talks to the bank.

No ids, no file names, and the one box that is not obvious gets a line.

### Intermediate example

> The orders service now waits for the payments service before it reserves
> stock.
>
> *(diagram: Browser → Orders API → Payments, then Orders API → Stock;
> edges labelled "POST /orders", "charge", "reserve")*
>
> The Orders API (our Node service) calls Payments first. Stock is only
> reserved after Payments approves, which is the change in PR #214. We
> confirmed it in the staging trace for order 5531. The open question is the
> timeout when Payments is slow.

### Advanced example

> `reserve()` now runs after `charge()` resolves, which closes the
> oversell race.
>
> *(sequence diagram with activations and the error path)*
>
> The race window was the 40–200 ms between reserve and charge. Blast radius:
> checkout only. Next: add the idempotency key on retry.

## Persisted docs versus replies

In a lore doc, set the level with `%% level: <level>` inside the fence, so
the lint applies the right cap. In a reply, match the level of the reply's
prose. A Mermaid fence counts as code in the plain-english styles. Diagram
skills run when a picture was asked for or the answer has a shape, which
is the "the reader asked" case those styles allow. Keep the explanation
within the style's word budget and leave the fence out of the count.
