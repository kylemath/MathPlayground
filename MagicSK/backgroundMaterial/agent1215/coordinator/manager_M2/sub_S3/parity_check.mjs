/**
 * Node parity check against control_ensembles.py output anchors.
 * Run: node parity_check.mjs
 */
import {
  seedToState,
  deriveReplicateSeed,
  fisherYates,
  swapEnsembleForKValues,
  energyMetrics,
  PERM_DOMAIN,
  SWAP_DOMAIN,
} from "./control_ensembles.js";

const base = [1, 2, 15, 16, 12, 14, 3, 5, 13, 7, 10, 4, 8, 11, 6, 9];
const squareId = 1;
const seed = 1215;
const protocol = {
  pairSampling: "distinct_pairs_no_replacement",
  acrossK: "paired_prefix",
};

const permState = seedToState(deriveReplicateSeed(seed, squareId, 0, PERM_DOMAIN));
const { arr: permHead } = fisherYates(base.slice(), permState);

const swapState = seedToState(deriveReplicateSeed(seed, squareId, 0, SWAP_DOMAIN));
const { traces } = swapEnsembleForKValues(base, [1, 2, 3], swapState, protocol);
const swap1Residual = energyMetrics(traces[1].flat, 1).residual;

const result = runControlEnsembleSummary(base, squareId, seed, 200, protocol);

function runControlEnsembleSummary(baseFlat, squareId, seed, nReplicates, swapProtocol) {
  const conditions = ["rand", "swap1", "swap2", "swap3"];
  const summaries = {};
  for (const cond of conditions) {
    const residuals = [];
    for (let rep = 0; rep < nReplicates; rep += 1) {
      let flat;
      if (cond === "rand") {
        let state = seedToState(deriveReplicateSeed(seed, squareId, rep, PERM_DOMAIN));
        flat = fisherYates(baseFlat.slice(), state).arr;
      } else {
        let state = seedToState(deriveReplicateSeed(seed, squareId, rep, SWAP_DOMAIN));
        const k = Number(cond.slice(-1));
        const { traces: t } = swapEnsembleForKValues(
          baseFlat,
          [1, 2, 3],
          state,
          swapProtocol,
        );
        flat = t[k].flat;
      }
      residuals.push(energyMetrics(flat, 1).residual);
    }
    const mean = residuals.reduce((a, b) => a + b, 0) / residuals.length;
    summaries[cond] = { mean_residual: mean };
  }
  return summaries;
}

console.log(
  JSON.stringify(
    {
      first_rand_perm_head: permHead.slice(0, 8),
      swap1_residual_rep0: swap1Residual,
      mean_residual: {
        rand: result.rand.mean_residual,
        swap1: result.swap1.mean_residual,
        swap2: result.swap2.mean_residual,
        swap3: result.swap3.mean_residual,
      },
    },
    null,
    2,
  ),
);
