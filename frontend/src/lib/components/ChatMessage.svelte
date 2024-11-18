<script>
  import { ThumbUp, ThumbDown } from 'lucide-svelte';
  export let message;
  export let sessionId;

  let feedback = null;

  async function handleFeedback(type) {
    if (feedback === type) {
      // Clicking the same button again removes the feedback
      feedback = null;
    } else {
      feedback = type;
    }

    try {
      await fetch(`/api/chat/feedback/${message.id}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          feedback_type: type,
          session_id: sessionId
        })
      });
    } catch (error) {
      console.error('Failed to save feedback:', error);
    }
  }
</script>

<div class="message {message.role}">
  <div class="content">
    {#if message.role === 'assistant'}
      {@html marked(message.content)}
    {:else}
      {message.content}
    {/if}
  </div>
  
  {#if message.role === 'assistant'}
    <div class="feedback">
      <button 
        class="feedback-btn {feedback === 'like' ? 'active' : ''}"
        on:click={() => handleFeedback('like')}
      >
        <ThumbUp size={18} />
      </button>
      <button 
        class="feedback-btn {feedback === 'dislike' ? 'active' : ''}"
        on:click={() => handleFeedback('dislike')}
      >
        <ThumbDown size={18} />
      </button>
    </div>
  {/if}
</div>

<style>
  .feedback {
    display: flex;
    gap: 0.5rem;
    margin-top: 0.5rem;
  }

  .feedback-btn {
    background: none;
    border: none;
    cursor: pointer;
    padding: 0.25rem;
    border-radius: 4px;
    color: #666;
    transition: all 0.2s;
  }

  .feedback-btn:hover {
    background: #eee;
  }

  .feedback-btn.active {
    color: #0066cc;
    background: #e6f0ff;
  }
</style> 