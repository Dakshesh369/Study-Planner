// Rotating "highlighter" palette assigned to subjects in order of creation.
export const SUBJECT_PALETTE = [
  "#5AA9A3", // teal
  "#E8543E", // coral
  "#D9A441", // amber
  "#8B7FD1", // violet
  "#5B8DEF", // blue
  "#4CAE7D", // green
  "#E27DBF", // pink
  "#C97C4B", // rust
];

export function colorForIndex(i) {
  return SUBJECT_PALETTE[i % SUBJECT_PALETTE.length];
}

export function buildColorMap(subjectNamesInOrder) {
  const map = {};
  subjectNamesInOrder.forEach((name, i) => {
    map[name] = colorForIndex(i);
  });
  return map;
}
