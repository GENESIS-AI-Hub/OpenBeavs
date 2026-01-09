<script lang="ts">
	import { onMount } from 'svelte';
	import { fade, fly } from 'svelte/transition';
	import Modal from '$lib/components/common/Modal.svelte';

	export let show = false;
	export let onReportClick: () => void;

	let dontShowAgain = false;
	let autoCloseTimer: ReturnType<typeof setTimeout> | null = null;

	onMount(() => {
		// Check if user has dismissed this before
		const dismissed = localStorage.getItem('betaWarningDismissed');
		if (!dismissed) {
			show = true;
			
			// Auto-close after 10 seconds
			autoCloseTimer = setTimeout(() => {
				if (show && !dontShowAgain) {
					handleClose();
				}
			}, 10000);
		}

		return () => {
			if (autoCloseTimer) {
				clearTimeout(autoCloseTimer);
			}
		};
	});

	const handleClose = () => {
		if (dontShowAgain) {
			localStorage.setItem('betaWarningDismissed', 'true');
		}
		show = false;
		if (autoCloseTimer) {
			clearTimeout(autoCloseTimer);
		}
	};

	const handleReportClick = () => {
		handleClose();
		onReportClick();
	};
</script>

{#if show}
	<Modal bind:show size="sm">
		<div class="px-6 py-5">
			<!-- Icon -->
			<div class="flex justify-center mb-4">
				<div
					class="w-16 h-16 rounded-full bg-gradient-to-br from-amber-400 to-orange-500 flex items-center justify-center"
				>
					<svg
						xmlns="http://www.w3.org/2000/svg"
						class="h-8 w-8 text-white"
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
			</div>

			<!-- Title -->
			<h2 class="text-2xl font-bold text-center mb-3 dark:text-white">
				Beta Version
			</h2>

			<!-- Message -->
			<p class="text-center text-gray-600 dark:text-gray-300 mb-6">
				This site is in beta. Please report any issues you encounter to help us improve!
			</p>

			<!-- Buttons -->
			<div class="flex flex-col gap-3">
				<button
					on:click={handleReportClick}
					class="w-full px-4 py-3 rounded-lg bg-gradient-to-r from-blue-500 to-purple-600 text-white font-medium hover:from-blue-600 hover:to-purple-700 transition-all duration-200 transform hover:scale-[1.02] active:scale-[0.98] shadow-lg"
				>
					Report an Issue
				</button>

				<button
					on:click={handleClose}
					class="w-full px-4 py-2 rounded-lg bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 font-medium hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors duration-200"
				>
					Continue
				</button>
			</div>

			<!-- Don't show again checkbox -->
			<div class="mt-4 flex items-center justify-center">
				<label class="flex items-center cursor-pointer group">
					<input
						type="checkbox"
						bind:checked={dontShowAgain}
						class="w-4 h-4 rounded border-gray-300 dark:border-gray-600 text-blue-600 focus:ring-2 focus:ring-blue-500 focus:ring-offset-0 cursor-pointer"
					/>
					<span class="ml-2 text-sm text-gray-600 dark:text-gray-400 group-hover:text-gray-800 dark:group-hover:text-gray-200 transition-colors">
						Don't show this again
					</span>
				</label>
			</div>
		</div>
	</Modal>
{/if}

<style>
	/* Custom checkbox styling */
	input[type='checkbox'] {
		appearance: none;
		-webkit-appearance: none;
		background-color: white;
		border: 2px solid #d1d5db;
	}

	input[type='checkbox']:checked {
		background-color: #3b82f6;
		border-color: #3b82f6;
		background-image: url("data:image/svg+xml,%3csvg viewBox='0 0 16 16' fill='white' xmlns='http://www.w3.org/2000/svg'%3e%3cpath d='M12.207 4.793a1 1 0 010 1.414l-5 5a1 1 0 01-1.414 0l-2-2a1 1 0 011.414-1.414L6.5 9.086l4.293-4.293a1 1 0 011.414 0z'/%3e%3c/svg%3e");
		background-size: 100% 100%;
		background-position: center;
		background-repeat: no-repeat;
	}

	.dark input[type='checkbox'] {
		background-color: #374151;
		border-color: #4b5563;
	}

	.dark input[type='checkbox']:checked {
		background-color: #3b82f6;
		border-color: #3b82f6;
	}
</style>
