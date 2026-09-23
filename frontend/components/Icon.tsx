import React from "react";
import Svg, { Circle, Path, Rect } from "react-native-svg";

export type IconName =
  | "home"
  | "sparkle"
  | "plate"
  | "target"
  | "checklist"
  | "trophy"
  | "person"
  | "sun"
  | "moon"
  | "sliders"
  | "bell"
  | "lock"
  | "heart"
  | "collage"
  | "plus"
  | "dots";

type IconProps = {
  name: IconName;
  size?: number;
  color: string;
  strokeWidth?: number;
};

/**
 * A single, consistent line-icon family used across the whole app instead of
 * mismatched emoji. Every glyph shares the same stroke weight and rounded
 * caps/joins so the icon set reads as one considered system rather than a
 * grab-bag — that consistency is most of what makes it feel editorial.
 */
export function Icon({ name, size = 22, color, strokeWidth = 1.7 }: IconProps) {
  const stroke = { stroke: color, strokeWidth, strokeLinecap: "round" as const, strokeLinejoin: "round" as const, fill: "none" };

  return (
    <Svg width={size} height={size} viewBox="0 0 24 24">
      {name === "home" && (
        <>
          <Path d="M4 11.2 12 4l8 7.2" {...stroke} />
          <Path d="M6 10v8.5a1 1 0 0 0 1 1h3.2v-5.4h3.6v5.4H17a1 1 0 0 0 1-1V10" {...stroke} />
        </>
      )}

      {name === "sparkle" && <Path d="M12 3.2 13.7 9l5.8 1.7-5.8 1.7L12 18.2l-1.7-5.8L4.5 10.7l5.8-1.7Z" fill={color} />}

      {name === "plate" && (
        <>
          <Circle cx="12" cy="12" r="8.2" {...stroke} />
          <Circle cx="12" cy="12" r="3.1" {...stroke} />
        </>
      )}

      {name === "target" && (
        <>
          <Circle cx="12" cy="12" r="8.2" {...stroke} />
          <Circle cx="12" cy="12" r="4.6" {...stroke} />
          <Circle cx="12" cy="12" r="1.1" fill={color} stroke="none" />
        </>
      )}

      {name === "checklist" && (
        <>
          <Rect x="4.2" y="4.2" width="15.6" height="15.6" rx="3.4" {...stroke} />
          <Path d="M8 12.2 10.6 14.8 16 9.4" {...stroke} />
        </>
      )}

      {name === "trophy" && (
        <>
          <Path d="M8 5h8v4.4a4 4 0 0 1-8 0V5Z" {...stroke} />
          <Path d="M8 6.2H5.4A2.4 2.4 0 0 0 7.2 10" {...stroke} />
          <Path d="M16 6.2h2.6A2.4 2.4 0 0 1 16.8 10" {...stroke} />
          <Path d="M12 13.4v3.2M9 20h6M10 17h4l.6 3H9.4Z" {...stroke} />
        </>
      )}

      {name === "person" && (
        <>
          <Circle cx="12" cy="8.1" r="3.6" {...stroke} />
          <Path d="M4.6 19.4c.9-3.7 4-5.6 7.4-5.6s6.5 1.9 7.4 5.6" {...stroke} />
        </>
      )}

      {name === "sun" && (
        <>
          <Circle cx="12" cy="12" r="4" {...stroke} />
          <Path
            d="M12 2.8v2.1M12 19.1v2.1M21.2 12h-2.1M4.9 12H2.8M18.2 5.8l-1.5 1.5M7.3 16.7l-1.5 1.5M18.2 18.2l-1.5-1.5M7.3 7.3 5.8 5.8"
            {...stroke}
          />
        </>
      )}

      {name === "moon" && <Path d="M20 14.7A8.1 8.1 0 0 1 9.3 4a6.6 6.6 0 1 0 10.7 10.7Z" {...stroke} />}

      {name === "sliders" && (
        <>
          <Path d="M4.5 7h6.4M14.9 7h4.6M4.5 12h11.4M18.9 12h.6M4.5 17h2.6M10.1 17h9.4" {...stroke} />
          <Circle cx="12.7" cy="7" r="1.9" fill={color} stroke="none" />
          <Circle cx="17" cy="12" r="1.9" fill={color} stroke="none" />
          <Circle cx="8.1" cy="17" r="1.9" fill={color} stroke="none" />
        </>
      )}

      {name === "bell" && (
        <>
          <Path d="M6.4 16.2V11a5.6 5.6 0 1 1 11.2 0v5.2l1.4 2H5Z" {...stroke} />
          <Path d="M10.2 20.2a1.9 1.9 0 0 0 3.6 0" {...stroke} />
        </>
      )}

      {name === "lock" && (
        <>
          <Rect x="5.4" y="10.6" width="13.2" height="9.4" rx="2.4" {...stroke} />
          <Path d="M8.2 10.6V8a3.8 3.8 0 0 1 7.6 0v2.6" {...stroke} />
        </>
      )}

      {name === "heart" && (
        <Path
          d="M12 20S4 14.9 4 9.6A4.1 4.1 0 0 1 12 7.8 4.1 4.1 0 0 1 20 9.6C20 14.9 12 20 12 20Z"
          {...stroke}
        />
      )}

      {name === "collage" && (
        <>
          <Rect x="3.6" y="6.2" width="12.4" height="12.4" rx="2" {...stroke} />
          <Path d="M9.4 3.4h9.6a1.4 1.4 0 0 1 1.4 1.4v9.6" {...stroke} />
          <Circle cx="7.6" cy="9.6" r="1.1" fill={color} stroke="none" />
          <Path d="m4.4 16.6 3-3.3 2.4 2 3-3.6 2.6 3" {...stroke} />
        </>
      )}

      {name === "plus" && <Path d="M12 5v14M5 12h14" {...stroke} />}

      {name === "dots" && (
        <>
          <Circle cx="5.5" cy="12" r="1.6" fill={color} stroke="none" />
          <Circle cx="12" cy="12" r="1.6" fill={color} stroke="none" />
          <Circle cx="18.5" cy="12" r="1.6" fill={color} stroke="none" />
        </>
      )}
    </Svg>
  );
}
