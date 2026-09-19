import React from 'react';

interface BoundingBoxOverlayProps {
  imageUrl: string;
  imageAlt: string;
  boxes: { id: string; box: [number, number, number, number]; label: string }[];
  /** Native pixel dimensions the bounding boxes were computed against. */
  naturalWidth: number;
  naturalHeight: number;
}

export function BoundingBoxOverlay({ imageUrl, imageAlt, boxes, naturalWidth, naturalHeight }: BoundingBoxOverlayProps) {
  return (
    <div className="relative inline-block max-w-full">
      <img src={imageUrl} alt={imageAlt} className="max-w-full rounded-md" />
      {boxes.map(({ id, box, label }) => {
        const [x, y, w, h] = box;
        return (
          <div
            key={id}
            title={label}
            className="absolute border-2 border-red-500"
            style={{
              left: `${(x / naturalWidth) * 100}%`,
              top: `${(y / naturalHeight) * 100}%`,
              width: `${(w / naturalWidth) * 100}%`,
              height: `${(h / naturalHeight) * 100}%`,
            }}
          />
        );
      })}
    </div>
  );
}