import React from 'react';
import styled from 'styled-components';

const AxiomLoader = () => {
  return (
    <StyledWrapper>
      <div className="loader">
        {/* SVG Gradient Definitions */}
        <svg height={0} width={0} viewBox="0 0 100 100" className="absolute">
          <defs>
            <linearGradient id="grad-a" gradientUnits="userSpaceOnUse" x1={0} y1={100} x2={0} y2={0}>
              <stop stopColor="#0369a1" />
              <stop stopColor="#67e8f9" offset="1.5" />
            </linearGradient>
            <linearGradient id="grad-x" gradientUnits="userSpaceOnUse" x1={0} y1={100} x2={0} y2={0}>
              <stop stopColor="#0284c7" />
              <stop stopColor="#38bdf8" offset="1" />
            </linearGradient>
            <linearGradient id="grad-i" gradientUnits="userSpaceOnUse" x1={0} y1={100} x2={0} y2={0}>
              <stop stopColor="#0369a1" />
              <stop stopColor="#22d3ee" offset="1" />
            </linearGradient>
            <linearGradient id="grad-o" gradientUnits="userSpaceOnUse" x1={0} y1={100} x2={0} y2={0}>
              <stop stopColor="#38bdf8" />
              <stop stopColor="#075985" offset="1.5" />
            </linearGradient>
            <linearGradient id="grad-m" gradientUnits="userSpaceOnUse" x1={0} y1={100} x2={0} y2={0}>
              <stop stopColor="#0ea5e9" />
              <stop stopColor="#7dd3fc" offset="1" />
            </linearGradient>
          </defs>
        </svg>

        {/* 'A' */}
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 100 100" width={100} height={100} className="inline-block">
          <path strokeLinejoin="round" strokeLinecap="round" strokeWidth={8} stroke="url(#grad-a)" d="M 20,85 L 50,15 L 80,85 M 32,55 L 68,55" className="dash" id="A" pathLength={360} />
        </svg>

        {/* 'X' */}
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 100 100" width={100} height={100} className="inline-block">
          <path strokeLinejoin="round" strokeLinecap="round" strokeWidth={8} stroke="url(#grad-x)" d="M 20,20 L 80,80 M 80,20 L 20,80" className="dash" id="X" pathLength={360} />
        </svg>

        {/* 'I' */}
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 100 100" width={100} height={100} className="inline-block">
          <path strokeLinejoin="round" strokeLinecap="round" strokeWidth={8} stroke="url(#grad-i)" d="M 25,18 L 75,18 M 50,18 L 50,82 M 25,82 L 75,82" className="dash" id="I" pathLength={360} />
        </svg>

        {/* 'O' */}
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 100 100" width={100} height={100} className="inline-block">
          <path strokeLinejoin="round" strokeLinecap="round" strokeWidth={8} stroke="url(#grad-o)" d="M 50,16 C 28,16 20,30 20,50 C 20,70 28,84 50,84 C 72,84 80,70 80,50 C 80,30 72,16 50,16 Z" className="dash" id="O" pathLength={360} />
        </svg>

        {/* 'M' */}
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 100 100" width={100} height={100} className="inline-block">
          <path strokeLinejoin="round" strokeLinecap="round" strokeWidth={8} stroke="url(#grad-m)" d="M 18,85 L 18,18 L 50,55 L 82,18 L 82,85" className="dash" id="M" pathLength={360} />
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

export default AxiomLoader;