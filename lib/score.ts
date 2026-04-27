/**
 * Risk score model for an MCP tool / server / config.
 *
 * Score is 100 minus weighted deductions per finding. Weights are documented
 * on /methodology with the source for each (research agent 1 output).
 */

import type { StaticFinding } from "./detectors";

export type RiskTier = "clean" | "minor" | "concerning" | "high" | "critical";

export interface ScoreBreakdown {
  score: number;
  tier: RiskTier;
  deductions: { reason: string; points: number }[];
}

const HIDDEN_UNICODE_DEDUCTION = 30;
const COMMANDEERING_DEDUCTION = 20;
const HOMOGLYPH_DEDUCTION = 15;
const ENCODED_PAYLOAD_DEDUCTION = 10;
const FORWARD_REFERENCE_DEDUCTION = 10;
const MANIPULATION_PATTERN_DEDUCTION = 5;

const FORWARD_REFERENCE_RE =
  /\b(?:before|first|use)\s+(?:doc|the|another|other)\s+tool\b|MCP\s+Resource|mcpResource/i;

export const scoreFinding = (finding: StaticFinding, text = ""): ScoreBreakdown => {
  const deductions: { reason: string; points: number }[] = [];
  let score = 100;

  if (finding.invisible_char_count > 0) {
    deductions.push({
      reason: `Hidden Unicode bytes (${finding.invisible_char_count} codepoint${finding.invisible_char_count === 1 ? "" : "s"})`,
      points: HIDDEN_UNICODE_DEDUCTION,
    });
    score -= HIDDEN_UNICODE_DEDUCTION;
  }

  if (finding.manipulation_patterns.length >= 2) {
    deductions.push({
      reason: `Agent commandeering language (${finding.manipulation_patterns.length} imperatives)`,
      points: COMMANDEERING_DEDUCTION,
    });
    score -= COMMANDEERING_DEDUCTION;
  } else if (finding.manipulation_patterns.length === 1) {
    deductions.push({
      reason: `Manipulation pattern (1 imperative)`,
      points: MANIPULATION_PATTERN_DEDUCTION,
    });
    score -= MANIPULATION_PATTERN_DEDUCTION;
  }

  if (finding.homoglyph_flags > 0) {
    deductions.push({
      reason: `Latin homoglyph chars (${finding.homoglyph_flags})`,
      points: HOMOGLYPH_DEDUCTION,
    });
    score -= HOMOGLYPH_DEDUCTION;
  }

  if (finding.encoded_payloads > 0) {
    deductions.push({
      reason: `Encoded payload decoded to text (${finding.encoded_payloads})`,
      points: ENCODED_PAYLOAD_DEDUCTION,
    });
    score -= ENCODED_PAYLOAD_DEDUCTION;
  }

  if (finding.exfiltration_patterns.length > 0) {
    deductions.push({
      reason: `Exfiltration patterns (${finding.exfiltration_patterns.length})`,
      points: COMMANDEERING_DEDUCTION,
    });
    score -= COMMANDEERING_DEDUCTION;
  }

  if (finding.instruction_tags.length > 0) {
    deductions.push({
      reason: `Instruction tags (${finding.instruction_tags.join(", ")})`,
      points: COMMANDEERING_DEDUCTION,
    });
    score -= COMMANDEERING_DEDUCTION;
  }

  if (text && FORWARD_REFERENCE_RE.test(text)) {
    deductions.push({
      reason: `Forward reference to another tool / resource`,
      points: FORWARD_REFERENCE_DEDUCTION,
    });
    score -= FORWARD_REFERENCE_DEDUCTION;
  }

  if (score < 0) score = 0;
  if (score > 100) score = 100;

  let tier: RiskTier;
  if (score >= 95) tier = "clean";
  else if (score >= 80) tier = "minor";
  else if (score >= 60) tier = "concerning";
  else if (score >= 30) tier = "high";
  else tier = "critical";

  return { score, tier, deductions };
};
