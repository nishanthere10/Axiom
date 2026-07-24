import React from 'react';
import styled from 'styled-components';

const AtlasLoader = () => {
  return (
    <StyledWrapper>
      <div className="loader">
        {/* SVG Gradient Definitions */}
        <svg height={0} width={0} viewBox="0 0 100 100" className="absolute">
          <defs>
            <linearGradient id="grad-a1" gradientUnits="userSpaceOnUse" x1={0} y1={100} x2={0} y2={0}>
              <stop stopColor="#0369a1" />
              <stop stopColor="#67e8f9" offset="1.5" />
            </linearGradient>
            <linearGradient id="grad-t" gradientUnits="userSpaceOnUse" x1={0} y1={100} x2={0} y2={0}>
              <stop stopColor="#0284c7" />
              <stop stopColor="#38bdf8" offset="1" />
            </linearGradient>
            <linearGradient id="grad-l" gradientUnits="userSpaceOnUse" x1={0} y1={100} x2={0} y2={0}>
              <stop stopColor="#0369a1" />
              <stop stopColor="#22d3ee" offset="1" />
            </linearGradient>
            <linearGradient id="grad-a2" gradientUnits="userSpaceOnUse" x1={0} y1={100} x2={0} y2={0}>
              <stop stopColor="#38bdf8" />
              <stop stopColor="#075985" offset="1.5" />
            </linearGradient>
            <linearGradient id="grad-s" gradientUnits="userSpaceOnUse" x1={0} y1={100} x2={0} y2={0}>
              <stop stopColor="#0ea5e9" />
              <stop stopColor="#7dd3fc" offset="1" />
            </linearGradient>
          </defs>
        </svg>

        {/* First 'A' */}
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 100 100" width={100} height={100} className="inline-block">
          <path strokeLinejoin="round" strokeLinecap="round" strokeWidth={8} stroke="url(#grad-a1)" d="M 20,85 L 50,15 L 80,85 M 32,55 L 68,55" className="dash" id="A1" pathLength={360} />
        </svg>

        {/* 'T' */}
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 100 100" width={100} height={100} className="inline-block">
          <path strokeLinejoin="round" strokeLinecap="round" strokeWidth={8} stroke="url(#grad-t)" d="M 15,18 L 85,18 M 50,18 L 50,85" className="dash" id="T" pathLength={360} />
        </svg>

        {/* 'L' */}
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 100 100" width={100} height={100} className="inline-block">
          <path strokeLinejoin="round" strokeLinecap="round" strokeWidth={8} stroke="url(#grad-l)" d="M 25,15 L 25,85 L 80,85" className="dash" id="L" pathLength={360} />
        </svg>

        {/* Second 'A' */}
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 100 100" width={100} height={100} className="inline-block">
          <path strokeLinejoin="round" strokeLinecap="round" strokeWidth={8} stroke="url(#grad-a2)" d="M 20,85 L 50,15 L 80,85 M 32,55 L 68,55" className="dash" id="A2" pathLength={360} />
        </svg>

        {/* 'S' */}
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 100 100" width={100} height={100} className="inline-block">
          <path strokeLinejoin="round" strokeLinecap="round" strokeWidth={8} stroke="url(#grad-s)" d="M 75,28 C 75,12 25,12 25,36 C 25,60 75,52 75,72 C 75,92 25,92 25,76" className="dash" id="S" pathLength={360} />
        </svg>
      </div>
    </StyledWrapper>
  );
};

const StyledWrapper = styled.div`
  .absolute {
    position: absolute;
  }

  .inline-block {
    display: inline-block;
  }

  .loader {
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0.25em 0;
  }

  .dash {
    animation: dashArray 2s ease-in-out infinite, dashOffset 2s linear infinite;
  }

  @keyframes dashArray {
    0% {
      stroke-dasharray: 0 1 359 0;
    }
    50% {
      stroke-dasharray: 0 359 1 0;
    }
    100% {
      stroke-dasharray: 359 1 0 0;
    }
  }

  @keyframes dashOffset {
    0% {
      stroke-dashoffset: 385;
    }
    100% {
      stroke-dashoffset: 5;
    }
  }
`;

export default AtlasLoader;