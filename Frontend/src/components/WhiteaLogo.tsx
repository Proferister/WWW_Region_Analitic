const WhiteaLogo = ({ size = 100 }: { size?: number }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 200 200"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <g transform="translate(100,100)">
      {/* Outer ring */}
      <ellipse
        rx="80"
        ry="30"
        fill="none"
        stroke="white"
        strokeWidth="8"
        transform="rotate(0)"
      />
      <ellipse
        rx="80"
        ry="30"
        fill="none"
        stroke="white"
        strokeWidth="8"
        transform="rotate(60)"
      />
      <ellipse
        rx="80"
        ry="30"
        fill="none"
        stroke="white"
        strokeWidth="8"
        transform="rotate(-60)"
      />
      {/* Center dot */}
      <circle r="14" fill="white" />
    </g>
  </svg>
)

export default WhiteaLogo
