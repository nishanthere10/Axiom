"use client"

import { Renderer, Program, Mesh, Color, Triangle } from 'ogl';
import { useEffect, useRef } from 'react';

const VERT = `#version 300 es
in vec2 position;
void main() {
  gl_Position = vec4(position, 0.0, 1.0);
}
`;

const FRAG = `#version 300 es
precision highp float;

uniform float uTime;
uniform float uAmplitude;
uniform vec3 uColorStops[5];
uniform vec2 uResolution;
uniform float uBlend;

out vec4 fragColor;

vec3 permute(vec3 x) {
  return mod(((x * 34.0) + 1.0) * x, 289.0);
}

float snoise(vec2 v){
  const vec4 C = vec4(
      0.211324865405187, 0.366025403784439,
      -0.577350269189626, 0.024390243902439
  );
  vec2 i  = floor(v + dot(v, C.yy));
  vec2 x0 = v - i + dot(i, C.xx);
  vec2 i1 = (x0.x > x0.y) ? vec2(1.0, 0.0) : vec2(0.0, 1.0);
  vec4 x12 = x0.xyxy + C.xxzz;
  x12.xy -= i1;
  i = mod(i, 289.0);

  vec3 p = permute(
      permute(i.y + vec3(0.0, i1.y, 1.0))
    + i.x + vec3(0.0, i1.x, 1.0)
  );

  vec3 m = max(
      0.5 - vec3(
          dot(x0, x0),
          dot(x12.xy, x12.xy),
          dot(x12.zw, x12.zw)
      ), 
      0.0
  );
  m = m * m;
  m = m * m;

  vec3 x = 2.0 * fract(p * C.www) - 1.0;
  vec3 h = abs(x) - 0.5;
  vec3 ox = floor(x + 0.5);
  vec3 a0 = x - ox;
  m *= 1.79284291400159 - 0.85373472095314 * (a0*a0 + h*h);

  vec3 g;
  g.x  = a0.x  * x0.x  + h.x  * x0.y;
  g.yz = a0.yz * x12.xz + h.yz * x12.yw;
  return 130.0 * dot(m, g);
}

void main() {
  vec2 uv = gl_FragCoord.xy / uResolution;
  
  float scaled = clamp(uv.x, 0.0, 0.9999) * 4.0;
  int idx = int(scaled);
  float lerpFactor = fract(scaled);
  
  vec3 c1, c2;
  if (idx == 0) { c1 = uColorStops[0]; c2 = uColorStops[1]; }
  else if (idx == 1) { c1 = uColorStops[1]; c2 = uColorStops[2]; }
  else if (idx == 2) { c1 = uColorStops[2]; c2 = uColorStops[3]; }
  else { c1 = uColorStops[3]; c2 = uColorStops[4]; }
  
  vec3 rampColor = mix(c1, c2, lerpFactor);
  
  float height = snoise(vec2(uv.x * 2.2 + uTime * 0.12, uTime * 0.25)) * 0.6 * uAmplitude;
  height = exp(height);
  height = (uv.y * 2.0 - height + 0.2);
  float intensity = 0.9 * height;
  
  float midPoint = 0.10;
  float auroraAlpha = smoothstep(midPoint - uBlend * 0.5, midPoint + uBlend * 0.5, intensity);
  
  vec3 auroraColor = intensity * rampColor;
  
  fragColor = vec4(auroraColor * auroraAlpha, auroraAlpha);
}
`;

export default function Aurora(props) {
  const { colorStops = ['#020617', '#1e3a8a', '#2563eb', '#38bdf8', '#00f2fe'], amplitude = 1.0, blend = 0.5 } = props;
  const propsRef = useRef(props);
  propsRef.current = props;

  const ctnDom = useRef(null);

  useEffect(() => {
    const ctn = ctnDom.current;
    if (!ctn) return;

    // Removed prefers-reduced-motion early return so the dynamic WebGL shader always mounts and animates
    const renderer = new Renderer({
      alpha: true,
      premultipliedAlpha: true,
      antialias: false,
      powerPreference: 'high-performance',
      dpr: Math.min(window.devicePixelRatio || 1, 1.5)
    });
    const gl = renderer.gl;
    gl.clearColor(0, 0, 0, 0);
    gl.enable(gl.BLEND);
    gl.blendFunc(gl.ONE, gl.ONE_MINUS_SRC_ALPHA);
    gl.canvas.style.backgroundColor = 'transparent';
    gl.canvas.setAttribute('aria-hidden', 'true');
    gl.canvas.setAttribute('role', 'presentation');

    let program;

    function resize() {
      if (!ctn) return;
      const width = ctn.offsetWidth;
      const height = ctn.offsetHeight;
      renderer.setSize(width, height);
      if (program) {
        program.uniforms.uResolution.value = [gl.canvas.width, gl.canvas.height];
      }
    }
    window.addEventListener('resize', resize);

    const geometry = new Triangle(gl);
    if (geometry.attributes.uv) {
      delete geometry.attributes.uv;
    }

    const colorStopsArray = colorStops.map(hex => {
      const c = new Color(hex);
      return [c.r, c.g, c.b];
    });

    program = new Program(gl, {
      vertex: VERT,
      fragment: FRAG,
      uniforms: {
        uTime: { value: 0 },
        uAmplitude: { value: amplitude },
        uColorStops: { value: colorStopsArray },
        uResolution: { value: [gl.canvas.width || ctn.offsetWidth, gl.canvas.height || ctn.offsetHeight] },
        uBlend: { value: blend }
      }
    });

    const mesh = new Mesh(gl, { geometry, program });
    ctn.appendChild(gl.canvas);

    let animateId = 0;
    let isVisible = true;
    let lastColorStops = null;
    let cachedColorStopsArray = colorStopsArray;

    const update = t => {
      if (!isVisible) {
        animateId = 0;
        return;
      }
      animateId = requestAnimationFrame(update);
      const { time = t * 0.01, speed = 1.0, amplitude: currentAmp = 1.0, blend: currentBlend = blend, colorStops: currentStops = colorStops } = propsRef.current;
      
      program.uniforms.uTime.value = time * speed * 0.1;
      program.uniforms.uAmplitude.value = currentAmp;
      program.uniforms.uBlend.value = currentBlend;
      
      if (currentStops !== lastColorStops) {
        lastColorStops = currentStops;
        cachedColorStopsArray = currentStops.map(hex => {
          const c = new Color(hex);
          return [c.r, c.g, c.b];
        });
        program.uniforms.uColorStops.value = cachedColorStopsArray;
      }
      
      renderer.render({ scene: mesh });
    };

    const observer = new IntersectionObserver(([entry]) => {
      isVisible = entry.isIntersecting;
      if (isVisible && !animateId) {
        animateId = requestAnimationFrame(update);
      } else if (!isVisible && animateId) {
        cancelAnimationFrame(animateId);
        animateId = 0;
      }
    });
    observer.observe(ctn);

    animateId = requestAnimationFrame(update);

    resize();

    return () => {
      observer.disconnect();
      if (animateId) cancelAnimationFrame(animateId);
      window.removeEventListener('resize', resize);
      if (ctn && gl.canvas.parentNode === ctn) {
        ctn.removeChild(gl.canvas);
      }
      gl.getExtension('WEBGL_lose_context')?.loseContext();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [amplitude]);

  return (
    <div ref={ctnDom} className="w-full h-full relative" aria-hidden="true">
      <div className="absolute inset-0 bg-gradient-to-br from-[#020617] via-[#1e3a8a]/30 to-[#38bdf8]/20 -z-10 pointer-events-none" />
    </div>
  );
}
