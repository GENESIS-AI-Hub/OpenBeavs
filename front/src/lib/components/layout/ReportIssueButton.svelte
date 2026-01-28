<script lang="ts">
	import { onMount } from 'svelte';
	import { fade, scale } from 'svelte/transition';

	export let onClick: () => void;

	let showTooltip = false;
	let tooltipTimeout: ReturnType<typeof setTimeout> | null = null;

	const handleMouseEnter = () => {
		tooltipTimeout = setTimeout(() => {
			showTooltip = true;
		}, 500);
	};

	const handleMouseLeave = () => {
		if (tooltipTimeout) {
			clearTimeout(tooltipTimeout);
		}
		showTooltip = false;
	};

	const handleClick = () => {
		showTooltip = false;
		onClick();
	};
</script>

<div class="fixed bottom-6 right-6 z-40">
	<!-- Tooltip -->
	{#if showTooltip}
		<div
			transition:fade={{ duration: 150 }}
			class="absolute bottom-full right-0 mb-2 px-3 py-2 bg-gray-900 dark:bg-gray-700 text-white text-sm rounded-lg shadow-lg whitespace-nowrap"
		>
			Report an Issue
			<div class="absolute top-full right-4 w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-gray-900 dark:border-t-gray-700"></div>
		</div>
	{/if}

	<!-- Floating Action Button -->
	<button
		on:click={handleClick}
		on:mouseenter={handleMouseEnter}
		on:mouseleave={handleMouseLeave}
		class="report-button group relative w-14 h-14 rounded-full bg-gradient-to-br from-blue-500 via-purple-500 to-pink-500 shadow-lg hover:shadow-2xl transition-all duration-300 flex items-center justify-center overflow-hidden"
		aria-label="Report an issue"
	>
		<!-- Pulse animation ring -->
		<div class="absolute inset-0 rounded-full bg-gradient-to-br from-blue-400 to-purple-400 animate-ping opacity-20"></div>
		
		<!-- Button content -->
		<div class="relative z-10 transform group-hover:scale-110 transition-transform duration-200">
			<svg
				xmlns="http://www.w3.org/2000/svg"
				class="h-6 w-6 text-white"
				fill="none"
				viewBox="0 0 24 24"
				stroke="currentColor"
			>
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					stroke-width="2"
					d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
				/>
			</svg>
		</div>

		<!-- Hover glow effect -->
		<div class="absolute inset-0 rounded-full bg-white opacity-0 group-hover:opacity-20 transition-opacity duration-300"></div>
	</button>
</div>

<style>
	.report-button {
		animation: float 3s ease-in-out infinite;
	}

	@keyframes float {
		0%, 100% {
			transform: translateY(0px);
		}
		50% {
			transform: translateY(-10px);
		}
	}

	.report-button:hover {
		animation: none;
	}

	.report-button:active {
		transform: scale(0.95);
	}

	@keyframes ping {
		75%, 100% {
			transform: scale(1.5);
			opacity: 0;
		}
	}

	.animate-ping {
		animation: ping 2s cubic-bezier(0, 0, 0.2, 1) infinite;
	}

	/* Responsive adjustments */
	@media (max-width: 640px) {
		:global(.fixed.bottom-6.right-6) {
			bottom: 1rem;
			right: 1rem;
		}
	}
</style>
