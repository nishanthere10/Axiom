// GlassIcons — all colors now use CSS variables from the design system.
// Gradients map to the project's --primary, --success, --destructive etc. tokens.

const gradientMapping = {
  blue:   'linear-gradient(hsl(var(--primary)), hsl(217.2 91.2% 45%))',
  purple: 'linear-gradient(hsl(283 90% 50%), hsl(268 90% 50%))',
  red:    'linear-gradient(hsl(var(--destructive)), hsl(0 62.8% 22%))',
  indigo: 'linear-gradient(hsl(238 84% 65%), hsl(253 84% 55%))',
  orange: 'linear-gradient(hsl(32 95% 55%), hsl(20 95% 45%))',
  green:  'linear-gradient(hsl(var(--success)), hsl(142.1 76.2% 25%))',
};

const GlassIcons = ({ items, className }) => {
  const getBackgroundStyle = color => {
    if (gradientMapping[color]) {
      return { background: gradientMapping[color] };
    }
    return { background: color };
  };

  return (
    <div className={`grid gap-[5em] grid-cols-2 md:grid-cols-3 mx-auto py-[3em] overflow-visible ${className || ''}`}>
      {items.map((item, index) => (
        <button
          key={index}
          type="button"
          aria-label={item.label}
          className={`relative bg-transparent outline-none border-none cursor-pointer w-[4.5em] h-[4.5em] [perspective:24em] [transform-style:preserve-3d] [-webkit-tap-highlight-color:transparent] group ${
            item.customClass || ''
          }`}
        >
          <span
            className="absolute top-0 left-0 w-full h-full rounded-[1.25em] block transition-[opacity,transform] duration-300 ease-[cubic-bezier(0.83,0,0.17,1)] origin-[100%_100%] rotate-[15deg] [will-change:transform] group-hover:[transform:rotate(25deg)_translate3d(-0.5em,-0.5em,0.5em)]"
            style={{
              ...getBackgroundStyle(item.color),
              boxShadow: '0.5em -0.5em 0.75em hsla(223, 10%, 10%, 0.15)'
            }}
          ></span>

          <span
            className="absolute top-0 left-0 w-full h-full rounded-[1.25em] bg-[hsla(0,0%,100%,0.15)] transition-[opacity,transform] duration-300 ease-[cubic-bezier(0.83,0,0.17,1)] origin-[80%_50%] flex backdrop-blur-[0.75em] [-webkit-backdrop-filter:blur(0.75em)] [-moz-backdrop-filter:blur(0.75em)] [will-change:transform] transform group-hover:[transform:translate3d(0,0,2em)]"
            style={{
              boxShadow: '0 0 0 0.1em hsla(0, 0%, 100%, 0.3) inset'
            }}
          >
            <span className="m-auto w-[1.5em] h-[1.5em] flex items-center justify-center" aria-hidden="true">
              {item.icon}
            </span>
          </span>

          <span className="absolute top-full left-0 right-0 text-center whitespace-nowrap leading-[2] text-base opacity-0 transition-[opacity,transform] duration-300 ease-[cubic-bezier(0.83,0,0.17,1)] translate-y-0 group-hover:opacity-100 group-hover:[transform:translateY(20%)]">
            {item.label}
          </span>
        </button>
      ))}
    </div>
  );
};

export default GlassIcons;
