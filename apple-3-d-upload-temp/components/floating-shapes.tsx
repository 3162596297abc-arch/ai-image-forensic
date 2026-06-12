"use client";

import { useEffect, useState } from "react";
import { cn } from "@/lib/utils";

interface Shape {
  id: number;
  size: number;
  x: number;
  y: number;
  delay: number;
  duration: number;
  opacity: number;
}

export function FloatingShapes() {
  const [shapes, setShapes] = useState<Shape[]>([]);

  useEffect(() => {
    const generatedShapes: Shape[] = Array.from({ length: 6 }, (_, i) => ({
      id: i,
      size: Math.random() * 200 + 100,
      x: Math.random() * 100,
      y: Math.random() * 100,
      delay: Math.random() * 5,
      duration: Math.random() * 10 + 15,
      opacity: Math.random() * 0.03 + 0.02,
    }));
    setShapes(generatedShapes);
  }, []);

  return (
    <div className="fixed inset-0 overflow-hidden pointer-events-none">
      {shapes.map((shape) => (
        <div
          key={shape.id}
          className={cn(
            "absolute rounded-full",
            "bg-gradient-to-br from-accent/30 to-accent/10",
            "blur-3xl"
          )}
          style={{
            width: shape.size,
            height: shape.size,
            left: `${shape.x}%`,
            top: `${shape.y}%`,
            opacity: shape.opacity,
            animation: `float ${shape.duration}s ease-in-out ${shape.delay}s infinite alternate`,
          }}
        />
      ))}
      
      <style jsx>{`
        @keyframes float {
          0% {
            transform: translate(0, 0) scale(1);
          }
          100% {
            transform: translate(30px, -30px) scale(1.1);
          }
        }
      `}</style>
    </div>
  );
}
