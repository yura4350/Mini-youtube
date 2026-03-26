<template>
  <main class="home-shell">
    <section class="home-hero">
      <p class="kicker">MEDIA HUB PLATFORM</p>
      <h1>Build Your YouTube-Style Video Platform</h1>
      <p>
        The authentication foundation is ready: login, registration, and profile management. Next,
        you can move on to feed, upload, and video playback pages.
      </p>
      <div class="cta-row">
        <RouterLink to="/login" class="btn-main">Sign In</RouterLink>
        <RouterLink to="/register" class="btn-ghost">Create Account</RouterLink>
      </div>
    </section>
  </main>
</template>

<style scoped>
.home-shell {
  min-height: calc(100vh - 68px);
  display: grid;
  place-items: center;
  padding: 24px;
}

.home-hero {
  max-width: 720px;
  text-align: center;
  padding: 34px;
  border-radius: 20px;
  border: 1px solid rgba(255, 255, 255, 0.14);
  background: linear-gradient(165deg, rgba(220, 38, 38, 0.2), rgba(26, 26, 26, 0.94));
}

.kicker {
  color: #f87171;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.15em;
}

h1 {
  margin: 12px 0;
  font-size: clamp(30px, 5vw, 50px);
  line-height: 1.1;
  color: #fff;
}

p {
  color: #d6d9e1;
}

.cta-row {
  margin-top: 18px;
  display: flex;
  justify-content: center;
  gap: 10px;
}

.btn-main,
.btn-ghost {
  text-decoration: none;
  padding: 11px 16px;
  border-radius: 10px;
  font-weight: 600;
}

.btn-main {
  background: linear-gradient(135deg, #dc2626, #ef4444);
  color: #fff;
}

.btn-ghost {
  border: 1px solid rgba(255, 255, 255, 0.28);
  color: #fff;
}

@media (max-width: 740px) {
  .home-hero {
    text-align: left;
  }

  .cta-row {
    justify-content: flex-start;
    flex-wrap: wrap;
  }
}
</style>
