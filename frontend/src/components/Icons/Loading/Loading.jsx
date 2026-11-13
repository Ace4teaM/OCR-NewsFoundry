const Loading = ({
    size = "1rem",
    ...props
}) => {
    return (
         <svg
            width={size}
            height={size}
            viewBox="0 0 48 48"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
            role="status"
            aria-hidden="true"
            stroke="currentColor"
            color="currentColor"
        >
            <circle
                cx="24"
                cy="24"
                r="19"
                stroke="currentColor"
                strokeWidth="4"
                opacity="0.15"
            />
            <path
                d="M43 24A19 19 0 0 0 24 5"
                stroke="currentColor"
                strokeWidth="4"
                strokeLinecap="round"
            >
                <animateTransform
                    attributeName="transform"
                    type="rotate"
                    from="0 24 24"
                    to="360 24 24"
                    dur="0.8s"
                    repeatCount="indefinite"
                />
            </path>
        </svg>
    );
};

export default Loading;