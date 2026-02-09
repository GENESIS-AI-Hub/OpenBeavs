<script>
	import { onMount, tick } from 'svelte';
	import { page } from '$app/stores';
	import { toast } from 'svelte-sonner';
    import { WEBUI_BASE_URL } from '$lib/constants';

	let agentId = '';
	let agent = null;
	let messages = [];
	let input = '';
	let loading = false;
	let chatElement;

	const scrollToBottom = async () => {
		await tick();
		if (chatElement) {
			chatElement.scrollTop = chatElement.scrollHeight;
		}
	};

	onMount(async () => {
		agentId = $page.url.searchParams.get('agent_id');
        const agentUrl = $page.url.searchParams.get('agent_url');

        // If provided a direct model/agent ID via URL
        if (!agentId && $page.url.searchParams.get('model')) {
            agentId = $page.url.searchParams.get('model');
        }

		if (agentId) {
			// Load local history
			const saved = localStorage.getItem(`embed_chat_${agentId}`);
			if (saved) {
				try {
					messages = JSON.parse(saved);
				} catch (e) {
					console.error('Failed to parse saved chat', e);
				}
			}

			// Fetch agent details
			try {
				const res = await fetch(`/api/embed/agent/${agentId}`);
				if (res.ok) {
					agent = await res.json();
				} else {
					toast.error('Failed to load agent details');
				}
			} catch (e) {
				console.error(e);
				toast.error('Error loading agent');
			}
		} else {
             toast.error("No agent specified");
        }
        
        scrollToBottom();
	});

	const saveChat = () => {
		if (agentId) {
			localStorage.setItem(`embed_chat_${agentId}`, JSON.stringify(messages));
		}
	};

	const submitMessage = async () => {
		if (!input.trim() || loading) return;

		const userMsg = { role: 'user', content: input };
		messages = [...messages, userMsg];
		input = '';
		loading = true;
		saveChat();
		scrollToBottom();

		try {
			const res = await fetch('/api/embed/chat/completions', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({
					model: agentId,
					messages: messages,
					stream: true
				})
			});

			if (!res.ok) {
				const err = await res.json();
				throw new Error(err.detail || 'Failed to send message');
			}

			// Handle streaming
			const reader = res.body.getReader();
			const decoder = new TextDecoder();
			let assistantMsg = { role: 'assistant', content: '' };
			messages = [...messages, assistantMsg];

			while (true) {
				const { done, value } = await reader.read();
				if (done) break;

				const chunk = decoder.decode(value);
				const lines = chunk.split('\n');
				
                for (const line of lines) {
					if (line.startsWith('data: ')) {
						const dataStr = line.slice(6);
						if (dataStr === '[DONE]') break;
						
                        try {
							const data = JSON.parse(dataStr);
							const delta = data.choices?.[0]?.delta?.content || '';
							assistantMsg.content += delta;
							messages = [...messages.slice(0, -1), assistantMsg];
                            scrollToBottom();
						} catch (e) {
							// ignore parse errors for partial chunks
						}
					}
				}
			}
            saveChat();

		} catch (e) {
			toast.error(e.message);
            messages = [...messages, { role: 'system', content: `Error: ${e.message}` }];
		} finally {
			loading = false;
            saveChat();
		}
	};
    
    const handleKeydown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            submitMessage();
        }
    }
</script>

<div class="flex flex-col h-screen bg-gray-50 dark:bg-gray-900 text-gray-800 dark:text-gray-100 font-primary">
	<!-- Header -->
	<div class="px-4 py-3 border-b dark:border-gray-800 flex items-center gap-3 bg-white dark:bg-gray-950">
		{#if agent}
			<img
				src={agent.profile_image_url || '/favicon.png'}
				alt={agent.name}
				class="w-8 h-8 rounded-full object-cover"
			/>
			<div>
				<h1 class="font-semibold text-sm">{agent.name}</h1>
				<p class="text-xs text-gray-500 dark:text-gray-400 line-clamp-1">{agent.description}</p>
			</div>
		{:else}
			<div class="w-8 h-8 rounded-full bg-gray-200 dark:bg-gray-800 animate-pulse"></div>
			<div class="flex-1">
				<div class="h-4 w-24 bg-gray-200 dark:bg-gray-800 rounded animate-pulse mb-1"></div>
				<div class="h-3 w-48 bg-gray-200 dark:bg-gray-800 rounded animate-pulse"></div>
			</div>
		{/if}
	</div>

	<!-- Chat Area -->
	<div class="flex-1 overflow-y-auto p-4 space-y-4" bind:this={chatElement}>
        {#if messages.length === 0}
            <div class="h-full flex flex-col items-center justify-center text-gray-400">
                <p>Start a conversation with {agent ? agent.name : 'the agent'}</p>
            </div>
        {/if}
        
		{#each messages as msg}
			<div class="flex {msg.role === 'user' ? 'justify-end' : 'justify-start'}">
				<div
					class="max-w-[85%] rounded-2xl px-4 py-2 {msg.role === 'user'
						? 'bg-blue-600 text-white rounded-br-none'
						: 'bg-white dark:bg-gray-800 border dark:border-gray-700 rounded-bl-none'}"
				>
                    <div class="whitespace-pre-wrap break-words text-sm">{msg.content}</div>
				</div>
			</div>
		{/each}
        
        {#if loading && messages[messages.length-1]?.role === 'user'}
             <div class="flex justify-start">
				<div class="bg-white dark:bg-gray-800 border dark:border-gray-700 rounded-2xl rounded-bl-none px-4 py-2">
                    <div class="flex gap-1">
                        <span class="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce"></span>
                        <span class="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce delay-100"></span>
                        <span class="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce delay-200"></span>
                    </div>
				</div>
			</div>
        {/if}
	</div>

	<!-- Input Area -->
	<div class="p-4 border-t dark:border-gray-800 bg-white dark:bg-gray-950">
		<div class="relative flex items-end gap-2 bg-gray-100 dark:bg-gray-850 rounded-xl border dark:border-gray-800 p-2">
			<textarea
				bind:value={input}
                on:keydown={handleKeydown}
				placeholder="Message..."
				class="w-full bg-transparent border-none focus:ring-0 resize-none max-h-32 min-h-[24px] py-1 text-sm outline-none"
				rows="1"
			></textarea>
			<button
				on:click={submitMessage}
				disabled={!input.trim() || loading}
				class="p-1.5 rounded-lg bg-blue-600 text-white disabled:opacity-50 disabled:cursor-not-allowed hover:bg-blue-700 transition"
			>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					width="16"
					height="16"
					viewBox="0 0 24 24"
					fill="none"
					stroke="currentColor"
					stroke-width="2"
					stroke-linecap="round"
					stroke-linejoin="round"
					class="lucide lucide-arrow-up"
					><path d="m5 12 7-7 7 7" /><path d="M12 19V5" /></svg
				>
			</button>
		</div>
	</div>
</div>
