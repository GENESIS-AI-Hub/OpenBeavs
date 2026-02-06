<script lang="ts">
	import { getContext } from 'svelte';
	import Modal from './common/Modal.svelte';

	const i18n = getContext('i18n');

	export let show = false;
	export let onConfirm = () => {};
</script>

<Modal bind:show size="lg" dismissible={false}>
	<div class="px-5 pt-4 dark:text-gray-300 text-gray-700">
		<div class="text-xl font-semibold">
			{$i18n.t('Privacy Notice')}
		</div>
	</div>

	<div class="w-full p-4 px-5 text-gray-700 dark:text-gray-100">
		<div class="overflow-y-auto max-h-96 scrollbar-hidden text-sm">
			<p class="mb-4">
				{$i18n.t('Welcome to OpenBeavs. Your privacy is important to us.')}
			</p>
			<p class="mb-2">
				{$i18n.t('Before you proceed to use our agents, please note the following:')}
			</p>
			<ul class="list-disc pl-5 mb-4 space-y-1">
				<li>{$i18n.t('Your interactions with the agents may be logged for quality assurance and training purposes.')}</li>
				<li>{$i18n.t('Please do not share sensitive personal information (PII) such as passwords, financial details, or health information.')}</li>
				<li>{$i18n.t('The data generated during your session is processed securely.')}</li>
			</ul>
			<p class="mb-4">
				{$i18n.t('By clicking "I Agree", you acknowledge that you have read and understood this notice.')}
			</p>
		</div>
		<div class="flex justify-end pt-3 text-sm font-medium">
			<button
				on:click={() => {
					show = false;
					onConfirm();
				}}
				class="px-4 py-2 text-sm font-medium bg-black hover:bg-gray-900 text-white dark:bg-white dark:text-black dark:hover:bg-gray-100 transition rounded-full"
			>
				{$i18n.t('I Agree')}
			</button>
		</div>
	</div>
</Modal>
