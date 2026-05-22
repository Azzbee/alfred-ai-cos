// Icon set ported from the Alfred prototype's inline SVGs (the `Ic.*` glyphs) plus
// the AlfMark logo. Stroke-based, currentColor-driven, sized by prop. Built on
// react-native-svg so they render identically to the web prototype.

import Svg, { Circle, Line, Path, Polyline, Rect } from "react-native-svg";

import { colors } from "@/theme/theme";

type IconProps = {
  size?: number;
  color?: string;
  stroke?: number;
};

// Shared wrapper: a 24-box viewBox, no fill, round caps/joins. Matches the
// prototype's lucide-style line icons.
function Line24({
  size = 20,
  color = colors.ink2,
  stroke = 1.6,
  children,
}: IconProps & { children: React.ReactNode }) {
  return (
    <Svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke={color}
      strokeWidth={stroke}
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      {children}
    </Svg>
  );
}

export const Ic = {
  Arrow: (p: IconProps) => (
    <Line24 {...p}>
      <Line x1={5} y1={12} x2={19} y2={12} />
      <Polyline points="12 5 19 12 12 19" />
    </Line24>
  ),
  ArrowUp: (p: IconProps) => (
    <Line24 {...p}>
      <Line x1={12} y1={19} x2={12} y2={5} />
      <Polyline points="5 12 12 5 19 12" />
    </Line24>
  ),
  Close: (p: IconProps) => (
    <Line24 {...p}>
      <Line x1={18} y1={6} x2={6} y2={18} />
      <Line x1={6} y1={6} x2={18} y2={18} />
    </Line24>
  ),
  Plus: (p: IconProps) => (
    <Line24 {...p}>
      <Line x1={12} y1={5} x2={12} y2={19} />
      <Line x1={5} y1={12} x2={19} y2={12} />
    </Line24>
  ),
  Check: (p: IconProps) => (
    <Line24 {...p}>
      <Polyline points="20 6 9 17 4 12" />
    </Line24>
  ),
  Snooze: (p: IconProps) => (
    <Line24 {...p}>
      <Circle cx={12} cy={13} r={8} />
      <Polyline points="12 9 12 13 14.5 14.5" />
      <Path d="M5 3 2 6" />
      <Path d="M19 3l3 3" />
    </Line24>
  ),
  Clock: (p: IconProps) => (
    <Line24 {...p}>
      <Circle cx={12} cy={12} r={9} />
      <Polyline points="12 7 12 12 16 14" />
    </Line24>
  ),
  Mic: (p: IconProps) => (
    <Line24 {...p}>
      <Rect x={9} y={3} width={6} height={11} rx={3} />
      <Path d="M5 11a7 7 0 0 0 14 0" />
      <Line x1={12} y1={18} x2={12} y2={21} />
    </Line24>
  ),
  Type: (p: IconProps) => (
    <Line24 {...p}>
      <Polyline points="4 7 4 4 20 4 20 7" />
      <Line x1={9} y1={20} x2={15} y2={20} />
      <Line x1={12} y1={4} x2={12} y2={20} />
    </Line24>
  ),
  Image: (p: IconProps) => (
    <Line24 {...p}>
      <Rect x={3} y={3} width={18} height={18} rx={2} />
      <Circle cx={8.5} cy={8.5} r={1.5} />
      <Polyline points="21 15 16 10 5 21" />
    </Line24>
  ),
  Forward: (p: IconProps) => (
    <Line24 {...p}>
      <Polyline points="15 17 20 12 15 7" />
      <Path d="M4 18v-2a4 4 0 0 1 4-4h12" />
    </Line24>
  ),
  Calendar: (p: IconProps) => (
    <Line24 {...p}>
      <Rect x={3} y={4} width={18} height={18} rx={2} />
      <Line x1={3} y1={9} x2={21} y2={9} />
      <Line x1={8} y1={2} x2={8} y2={6} />
      <Line x1={16} y1={2} x2={16} y2={6} />
    </Line24>
  ),
  User: (p: IconProps) => (
    <Line24 {...p}>
      <Path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
      <Circle cx={12} cy={7} r={4} />
    </Line24>
  ),
  Stack: (p: IconProps) => (
    <Line24 {...p}>
      <Polyline points="12 2 2 7 12 12 22 7 12 2" />
      <Polyline points="2 17 12 22 22 17" />
      <Polyline points="2 12 12 17 22 12" />
    </Line24>
  ),
  Bell: (p: IconProps) => (
    <Line24 {...p}>
      <Path d="M18 8a6 6 0 0 0-12 0c0 7-3 9-3 9h18s-3-2-3-9" />
      <Path d="M13.7 21a2 2 0 0 1-3.4 0" />
    </Line24>
  ),
  Mail: (p: IconProps) => (
    <Line24 {...p}>
      <Rect x={3} y={5} width={18} height={14} rx={2} />
      <Polyline points="3 7 12 13 21 7" />
    </Line24>
  ),
  Link: (p: IconProps) => (
    <Line24 {...p}>
      <Path d="M10 13a5 5 0 0 0 7 0l3-3a5 5 0 0 0-7-7l-1 1" />
      <Path d="M14 11a5 5 0 0 0-7 0l-3 3a5 5 0 0 0 7 7l1-1" />
    </Line24>
  ),
  Pause: (p: IconProps) => (
    <Line24 {...p}>
      <Rect x={7} y={5} width={3} height={14} rx={1} />
      <Rect x={14} y={5} width={3} height={14} rx={1} />
    </Line24>
  ),
  Refresh: (p: IconProps) => (
    <Line24 {...p}>
      <Polyline points="21 4 21 9 16 9" />
      <Path d="M3 11a9 9 0 0 1 15-6l3 3" />
      <Polyline points="3 20 3 15 8 15" />
      <Path d="M21 13a9 9 0 0 1-15 6l-3-3" />
    </Line24>
  ),
  Send: (p: IconProps) => (
    <Line24 {...p}>
      <Line x1={22} y1={2} x2={11} y2={13} />
      <Polyline points="22 2 15 22 11 13 2 9 22 2" />
    </Line24>
  ),
  Lock: (p: IconProps) => (
    <Line24 {...p}>
      <Rect x={5} y={11} width={14} height={10} rx={2} />
      <Path d="M8 11V7a4 4 0 0 1 8 0v4" />
    </Line24>
  ),
  Doc: (p: IconProps) => (
    <Line24 {...p}>
      <Path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <Polyline points="14 2 14 8 20 8" />
    </Line24>
  ),
  Sliders: (p: IconProps) => (
    <Line24 {...p}>
      <Line x1={4} y1={21} x2={4} y2={14} />
      <Line x1={4} y1={10} x2={4} y2={3} />
      <Line x1={12} y1={21} x2={12} y2={12} />
      <Line x1={12} y1={8} x2={12} y2={3} />
      <Line x1={20} y1={21} x2={20} y2={16} />
      <Line x1={20} y1={12} x2={20} y2={3} />
      <Line x1={1} y1={14} x2={7} y2={14} />
      <Line x1={9} y1={8} x2={15} y2={8} />
      <Line x1={17} y1={16} x2={23} y2={16} />
    </Line24>
  ),
  Today: (p: IconProps) => (
    <Line24 {...p}>
      <Rect x={3} y={4} width={18} height={18} rx={2} />
      <Line x1={3} y1={10} x2={21} y2={10} />
      <Line x1={8} y1={2} x2={8} y2={6} />
      <Line x1={16} y1={2} x2={16} y2={6} />
      <Circle cx={12} cy={16} r={2} />
    </Line24>
  ),
  Inbox: (p: IconProps) => (
    <Line24 {...p}>
      <Polyline points="22 12 16 12 14 15 10 15 8 12 2 12" />
      <Path d="M5.45 5.11 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z" />
    </Line24>
  ),
};

// The Albert logo glyph (阿福 → a calm rounded "A" mark). Filled or outline.
export function AlfMark({
  size = 20,
  color = colors.accent,
  filled = false,
}: {
  size?: number;
  color?: string;
  filled?: boolean;
}) {
  return (
    <Svg width={size} height={size} viewBox="0 0 24 24" fill="none">
      <Circle
        cx={12}
        cy={12}
        r={10}
        fill={filled ? color : "none"}
        stroke={color}
        strokeWidth={filled ? 0 : 1.6}
      />
      <Path
        d="M8.5 16.5 12 7l3.5 9.5"
        fill="none"
        stroke={filled ? "#fff" : color}
        strokeWidth={1.8}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <Line
        x1={9.7}
        y1={13.2}
        x2={14.3}
        y2={13.2}
        stroke={filled ? "#fff" : color}
        strokeWidth={1.8}
        strokeLinecap="round"
      />
    </Svg>
  );
}
