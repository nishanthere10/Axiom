import React from 'react';
import styled from 'styled-components';

const Card = () => {
  return (
    <StyledWrapper>
      <div className="card">
        <div className="content">
          <div className="word">UI</div>
          <div className="word">Experiment</div>
          <div className="word">UI</div>
        </div>
      </div>
    </StyledWrapper>
  );
}

const StyledWrapper = styled.div`
  .card {
    width: 190px;
    height: 254px;
    background: rgb(223, 225, 235);
    overflow: hidden;
    border-radius: 20px;
    box-shadow:
      inset 0px 56px 40px #2224,
      inset 0px -56px 40px #fff,
      1px 1px 2px #fff,
      -1px -1px 2px #4442;
  }

  .content {
    position: relative;
    display: flex;
    justify-content: space-between;
    align-items: center;
    width: 300%;
    height: 100%;
    transform: translateX(0%);
    animation: anim 6s infinite cubic-bezier(0.68, -0.55, 0.265, 1.55);
  }

  .word {
    width: 50%;
    text-align: center;
    color: #333;
    font-size: 30px;
    font-weight: 600;
    text-shadow: 9px 8px 3px #4443;
  }

  @keyframes anim {
    0% {
      transform: translateX(0%);
    }
    20% {
      transform: translateX(0%);
    }
    30% {
      transform: translateX(-33.33%);
    }
    70% {
      transform: translateX(-33.33%);
    }
    80% {
      transform: translateX(-66.66%);
    }
    100% {
      transform: translateX(-66.66%);
    }
  }`;

export default Card;
