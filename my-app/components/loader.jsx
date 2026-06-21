"use client";
import React from 'react';

const Loader = ({ scale = 1, color = "white", className = "" }) => {
  return (
    <div className={`loader-container ${className}`} style={{ transform: `scale(${scale})` }}>
      <style>{`
        .loader-container {
          position: relative;
          width: 50px;
          height: 50px;
        }
        .loader {
          position: absolute;
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%);
          width: 50px;
          height: 50px;
        }
        @keyframes loader_5191 {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        .square {
          background: ${color};
          width: 10px;
          height: 10px;
          position: absolute;
          top: 50%;
          left: 50%;
          margin-top: -5px;
          margin-left: -5px;
        }
        #sq1 { margin-top: -25px; margin-left: -25px; animation: loader_5191 675ms ease-in-out 0s infinite alternate; }
        #sq2 { margin-top: -25px; animation: loader_5191 675ms ease-in-out 75ms infinite alternate; }
        #sq3 { margin-top: -25px; margin-left: 15px; animation: loader_5191 675ms ease-in-out 150ms infinite; }
        #sq4 { margin-left: -25px; animation: loader_5191 675ms ease-in-out 225ms infinite; }
        #sq5 { animation: loader_5191 675ms ease-in-out 300ms infinite; }
        #sq6 { margin-left: 15px; animation: loader_5191 675ms ease-in-out 375ms infinite; }
        #sq7 { margin-top: 15px; margin-left: -25px; animation: loader_5191 675ms ease-in-out 450ms infinite; }
        #sq8 { margin-top: 15px; animation: loader_5191 675ms ease-in-out 525ms infinite; }
        #sq9 { margin-top: 15px; margin-left: 15px; animation: loader_5191 675ms ease-in-out 600ms infinite; }
      `}</style>
      <div className="loader">
        <div className="square" id="sq1" />
        <div className="square" id="sq2" />
        <div className="square" id="sq3" />
        <div className="square" id="sq4" />
        <div className="square" id="sq5" />
        <div className="square" id="sq6" />
        <div className="square" id="sq7" />
        <div className="square" id="sq8" />
        <div className="square" id="sq9" />
      </div>
    </div>
  );
}

export default Loader;
