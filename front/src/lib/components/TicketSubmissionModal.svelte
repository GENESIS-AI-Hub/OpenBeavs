<script lang="ts">
	import { onMount } from 'svelte';
	import { toast } from 'svelte-sonner';
	import Modal from '$lib/components/common/Modal.svelte';
	import confetti from 'canvas-confetti';

	export let show = false;

	let name = '';
	let email = '';
	let issueType = 'bug';
	let description = '';
	let isSubmitting = false;
	let showMetadata = false;

	// Auto-captured metadata
	let metadata = {
		userAgent: '',
		screenResolution: '',
		currentUrl: '',
		timestamp: '',
		userId: ''
	};

	// Validation errors
	let errors = {
		name: '',
		email: '',
		description: ''
	};

	onMount(() => {
		captureMetadata();
	});

	const captureMetadata = () => {
		metadata = {
			userAgent: navigator.userAgent,
			screenResolution: `${window.screen.width}x${window.screen.height}`,
			currentUrl: window.location.href,
			timestamp: new Date().toISOString(),
			userId: localStorage.getItem('userId') || 'Not logged in'
		};
	};

	const validateForm = (): boolean => {
		errors = { name: '', email: '', description: '' };
		let isValid = true;

		if (!name.trim()) {
			errors.name = 'Name is required';
			isValid = false;
		}

		const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
		if (!email.trim()) {
			errors.email = 'Email is required';
			isValid = false;
		} else if (!emailRegex.test(email)) {
			errors.email = 'Please enter a valid email address';
			isValid = false;
		}

		if (!description.trim()) {
			errors.description = 'Description is required';
			isValid = false;
		} else if (description.trim().length < 10) {
			errors.description = 'Description must be at least 10 characters';
			isValid = false;
		}

		return isValid;
	};

	const handleSubmit = async () => {
		if (!validateForm()) {
			toast.error('Please fix the errors before submitting');
			return;
		}

		isSubmitting = true;

		try {
			const response = await fetch('/api/v1/tickets/submit', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
					...(localStorage.token && { Authorization: `Bearer ${localStorage.token}` })
				},
				body: JSON.stringify({
					name: name.trim(),
					email: email.trim(),
					issue_type: issueType,
					description: description.trim(),
					metadata
				})
			});

			if (response.status === 429) {
				toast.error('Rate limit exceeded. Please try again later.');
				return;
			}

			if (!response.ok) {
				const error = await response.json();
				throw new Error(error.detail || 'Failed to submit ticket');
			}

			// Success!
			confetti({
				particleCount: 100,
				spread: 70,
				origin: { y: 0.6 }
			});

			toast.success('Ticket submitted successfully! We\'ll get back to you soon.');

			// Reset form
			name = '';
			email = '';
			issueType = 'bug';
			description = '';
			show = false;
		} catch (error) {
			console.error('Error submitting ticket:', error);
			toast.error(error.message || 'Failed to submit ticket. Please try again.');
		} finally {
			isSubmitting = false;
		}
	};

	$: if (show) {
		captureMetadata();
	}
</script>

{#if show}
	<Modal bind:show size="md">
		<div class="px-6 py-5">
			<!-- Header -->
			<div class="flex items-center justify-between mb-6">
				<h2 class="text-2xl font-bold dark:text-white">Report an Issue</h2>
				<button
					on:click={() => (show = false)}
					class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 transition-colors"
				>
					<svg
						xmlns="http://www.w3.org/2000/svg"
						class="h-6 w-6"
						fill="none"
						viewBox="0 0 24 24"
						stroke="currentColor"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M6 18L18 6M6 6l12 12"
						/>
					</svg>
				</button>
			</div>

			<!-- Form -->
			<form on:submit|preventDefault={handleSubmit} class="space-y-4">
				<!-- Name -->
				<div>
					<label for="name" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
						Name <span class="text-red-500">*</span>
					</label>
					<input
						id="name"
						type="text"
						bind:value={name}
						placeholder="Your name"
						class="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
						class:border-red-500={errors.name}
					/>
					{#if errors.name}
						<p class="mt-1 text-sm text-red-500">{errors.name}</p>
					{/if}
				</div>

				<!-- Email -->
				<div>
					<label for="email" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
						Email <span class="text-red-500">*</span>
					</label>
					<input
						id="email"
						type="email"
						bind:value={email}
						placeholder="your.email@example.com"
						class="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
						class:border-red-500={errors.email}
					/>
					{#if errors.email}
						<p class="mt-1 text-sm text-red-500">{errors.email}</p>
					{/if}
				</div>

				<!-- Issue Type -->
				<div>
					<label for="issueType" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
						Issue Type
					</label>
					<select
						id="issueType"
						bind:value={issueType}
						class="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
					>
						<option value="bug">Bug Report</option>
						<option value="feature_request">Feature Request</option>
						<option value="general_feedback">General Feedback</option>
					</select>
				</div>

				<!-- Description -->
				<div>
					<label for="description" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
						Description <span class="text-red-500">*</span>
					</label>
					<textarea
						id="description"
						bind:value={description}
						placeholder="Please describe the issue in detail..."
						rows="5"
						class="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all resize-none"
						class:border-red-500={errors.description}
					/>
					{#if errors.description}
						<p class="mt-1 text-sm text-red-500">{errors.description}</p>
					{/if}
					<p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
						{description.length} / 5000 characters (minimum 10)
					</p>
				</div>

				<!-- Auto-captured metadata (collapsible) -->
				<div class="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
					<button
						type="button"
						on:click={() => (showMetadata = !showMetadata)}
						class="w-full px-4 py-3 flex items-center justify-between bg-gray-50 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-750 transition-colors"
					>
						<span class="text-sm font-medium text-gray-700 dark:text-gray-300">
							Auto-captured Information
						</span>
						<svg
							xmlns="http://www.w3.org/2000/svg"
							class="h-5 w-5 text-gray-500 transition-transform"
							class:rotate-180={showMetadata}
							fill="none"
							viewBox="0 0 24 24"
							stroke="currentColor"
						>
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
						</svg>
					</button>

					{#if showMetadata}
						<div class="px-4 py-3 bg-white dark:bg-gray-900 text-xs space-y-2">
							<div>
								<span class="font-medium text-gray-600 dark:text-gray-400">Browser:</span>
								<span class="text-gray-800 dark:text-gray-200 ml-2">{metadata.userAgent}</span>
							</div>
							<div>
								<span class="font-medium text-gray-600 dark:text-gray-400">Screen:</span>
								<span class="text-gray-800 dark:text-gray-200 ml-2">{metadata.screenResolution}</span>
							</div>
							<div>
								<span class="font-medium text-gray-600 dark:text-gray-400">URL:</span>
								<span class="text-gray-800 dark:text-gray-200 ml-2">{metadata.currentUrl}</span>
							</div>
							<div>
								<span class="font-medium text-gray-600 dark:text-gray-400">Time:</span>
								<span class="text-gray-800 dark:text-gray-200 ml-2">{metadata.timestamp}</span>
							</div>
						</div>
					{/if}
				</div>

				<!-- Submit Button -->
				<div class="flex gap-3 pt-2">
					<button
						type="button"
						on:click={() => (show = false)}
						class="flex-1 px-4 py-3 rounded-lg bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 font-medium hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors duration-200"
						disabled={isSubmitting}
					>
						Cancel
					</button>
					<button
						type="submit"
						disabled={isSubmitting}
						class="flex-1 px-4 py-3 rounded-lg bg-gradient-to-r from-blue-500 to-purple-600 text-white font-medium hover:from-blue-600 hover:to-purple-700 transition-all duration-200 transform hover:scale-[1.02] active:scale-[0.98] shadow-lg disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none flex items-center justify-center"
					>
						{#if isSubmitting}
							<svg class="animate-spin h-5 w-5 mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
								<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
								<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
							</svg>
							Submitting...
						{:else}
							Submit Ticket
						{/if}
					</button>
				</div>
			</form>
		</div>
	</Modal>
{/if}

<style>
	.rotate-180 {
		transform: rotate(180deg);
	}
</style>
