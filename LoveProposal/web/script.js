(() => {
  'use strict';
  const $ = (selector) => document.querySelector(selector);
  const film = $('#film'), canvas = $('#particles'), context = canvas.getContext('2d');
  const startScreen = $('#startScreen'), startButton = $('#startButton'), audioNote = $('#audioNote'), music = $('#music');
  const soundButton = $('#soundButton'), soundLabel = $('#soundLabel'), caption = $('#caption'), proposal = $('#proposal'), ending = $('#ending');
  const boy = $('#boy'), girl = $('#girl'), progress = $('#progress'), sceneCount = $('#sceneCount'), status = $('#status'), city = $('#city');
  const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const scenes = [
    { text:'Some stories are written...', duration:3900, mode:'opening' },
    { text:'Some are found...', duration:3800, mode:'opening' },
    { text:'And some just happen.', duration:3600, mode:'city' },
    { text:'And then... he saw her.', duration:4300, mode:'notice' },
    { text:'Suddenly, nothing else mattered.', duration:4200, mode:'focused' },
    { text:'She became his favorite thought.', duration:3900, mode:'montage' },
    { text:'Every ordinary moment felt special.', duration:3900, mode:'montage' },
    { text:'Somehow... she became home.', duration:4000, mode:'montage' },
    { text:'With her, even the night felt brighter.', duration:4200, mode:'montage' },
    { text:'His heart already knew. It was always you.', duration:4600, mode:'heart' },
    { text:'He kept finding his way back to her.', duration:4800, mode:'walk' },
    { text:'I don\'t need a perfect life...', duration:3500, mode:'together' },
    { text:'I just want a life with you.', duration:4000, mode:'together' },
    { text:'There\'s only one question left...', duration:3500, mode:'kneel' }
  ];
  const state = { sceneIndex:-1, sceneStarted:0, running:false, accepted:false, lastFrame:0, width:0, height:0, dpr:1, stars:[], particles:[], fireworks:[], lastAmbient:0, audioStarted:false, audioContext:null, musicGain:null, musicVoices:[], chordTimer:0, chordIndex:0, audioMuted:false };

  function makeCity() {
    let seed = 73;
    const random = () => { seed = (seed * 16807) % 2147483647; return (seed - 1) / 2147483646; };
    for (let i = 0; i < 23; i += 1) {
      const building = document.createElement('i');
      building.className = 'building';
      building.style.setProperty('--building-width', `${3.4 + random() * 3.6}%`);
      building.style.setProperty('--building-height', `${30 + random() * 67}%`);
      building.style.setProperty('--window-light', `${0.25 + random() * 0.55}`);
      city.append(building);
    }
  }
  function resizeCanvas() {
    const rect = film.getBoundingClientRect();
    state.width = rect.width; state.height = rect.height; state.dpr = Math.min(devicePixelRatio || 1, 2);
    canvas.width = Math.round(state.width * state.dpr); canvas.height = Math.round(state.height * state.dpr);
    canvas.style.width = `${state.width}px`; canvas.style.height = `${state.height}px`;
    context.setTransform(state.dpr, 0, 0, state.dpr, 0, 0);
    state.stars = Array.from({ length:Math.max(90, Math.round(state.width * state.height / 4400)) }, () => ({ x:Math.random()*state.width, y:Math.random()*state.height*.74, radius:Math.random()*1.5+.35, phase:Math.random()*Math.PI*2, speed:Math.random()*2+.5 }));
  }
  function setCaption(text) {
    caption.classList.remove('is-visible');
    window.setTimeout(() => {
      if (!state.running || proposal.classList.contains('is-visible')) return;
      caption.textContent = ''; caption.classList.add('is-visible');
      let index = 0;
      const typeNext = () => {
        if (!caption.classList.contains('is-visible')) return;
        caption.textContent = text.slice(0, index++);
        if (index <= text.length) window.setTimeout(typeNext, reducedMotion ? 0 : 34);
      };
      typeNext();
    }, reducedMotion ? 0 : 420);
  }
  function enterScene(index) {
    if (index >= scenes.length) { showProposal(); return; }
    state.sceneIndex = index; state.sceneStarted = performance.now();
    const scene = scenes[index];
    film.classList.remove('is-focused','is-montage','is-finale'); boy.classList.remove('is-walking','is-kneeling'); girl.classList.remove('is-surprised');
    proposal.classList.remove('is-visible'); ending.classList.remove('is-visible');
    if (index >= 2) { boy.style.left = '35%'; girl.style.left = '67%'; }
    if (scene.mode === 'city') { boy.style.left = '36%'; boy.classList.add('is-walking'); }
    if (scene.mode === 'notice') { boy.classList.remove('is-walking'); film.classList.add('is-focused'); burst(state.width*.64,state.height*.52,16,'heart'); }
    if (['focused','montage','heart'].includes(scene.mode)) film.classList.add('is-focused');
    if (scene.mode === 'montage') {
      film.classList.add('is-montage');
      if (index % 2) { boy.style.left = '43%'; girl.style.left = '60%'; }
      state.lastAmbient = 0;
      for (let i=0;i<10;i+=1) addParticle(Math.random()*state.width,-10-Math.random()*state.height*.4,'petal');
    }
    if (scene.mode === 'heart') { burst(state.width*.43,state.height*.7,34,'heart'); state.lastAmbient = 0; }
    if (scene.mode === 'walk') { boy.classList.add('is-walking'); boy.style.left='53%'; girl.style.left='68%'; }
    if (scene.mode === 'together') { boy.classList.remove('is-walking'); boy.style.left='53%'; girl.style.left='68%'; }
    if (scene.mode === 'kneel') {
      boy.style.left='53%'; girl.style.left='68%';
      window.setTimeout(() => { if (state.sceneIndex === index) { boy.classList.add('is-kneeling'); girl.classList.add('is-surprised'); } },700);
    }
    sceneCount.textContent = `Chapter ${String(index+1).padStart(2,'0')} · ${String(scenes.length).padStart(2,'0')}`;
    setCaption(scene.text);
  }
  function showProposal() {
    state.sceneIndex=scenes.length; state.sceneStarted=performance.now(); state.running=false;
    boy.classList.remove('is-walking'); boy.classList.add('is-kneeling'); girl.classList.add('is-surprised');
    film.classList.add('is-focused','is-finale'); caption.classList.remove('is-visible'); proposal.classList.add('is-visible');
    proposal.setAttribute('aria-hidden','false'); ending.classList.remove('is-visible'); ending.setAttribute('aria-hidden','true');
    sceneCount.textContent='The question'; progress.style.width='100%'; status.textContent='The proposal is ready.';
    burst(state.width*.5,state.height*.56,90,'heart'); burst(state.width*.52,state.height*.52,55,'petal');
    launchFirework(state.width*.18,state.height*.29); launchFirework(state.width*.84,state.height*.25);
  }
  function addParticle(x,y,kind,burstMode=false) {
    const angle=Math.random()*Math.PI*2, speed=burstMode?80+Math.random()*350:13+Math.random()*35;
    state.particles.push({ x,y,vx:Math.cos(angle)*speed,vy:Math.sin(angle)*speed-(kind==='petal'?45:0),life:0,maxLife:burstMode?1.5+Math.random()*2.2:4.5+Math.random()*6,size:kind==='heart'?5+Math.random()*8:2+Math.random()*6,rotation:Math.random()*Math.PI*2,spin:(Math.random()-.5)*5,kind,burst:burstMode,color:Math.random()>.5?'#f595b4':'#ffd6ac' });
    if(state.particles.length>950) state.particles.splice(0,state.particles.length-950);
  }
  function burst(x,y,amount,kind) { for(let i=0;i<amount;i+=1) addParticle(x,y,kind||(Math.random()>.53?'heart':'petal'),true); }
  function launchFirework(x,y) { state.fireworks.push({x,y,life:0,duration:1.3,color:Math.random()>.5?'#ffcc9b':'#ff91b6'}); }
  async function startSynthMusic() {
    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    if (!AudioContextClass) return false;
    if (!state.audioContext) {
      state.audioContext = new AudioContextClass();
      state.musicGain = state.audioContext.createGain();
      state.musicGain.gain.value = 0.72;
      state.musicGain.connect(state.audioContext.destination);
    }
    await state.audioContext.resume();
    state.audioMuted = false;
    playChord(state.chordIndex);
    return true;
  }
  function playChord(index) {
    if (!state.audioContext || state.audioMuted) return;
    const chords = [[73.42,146.83,174.61,220,261.63],[55,110,146.83,174.61,220],[65.41,130.81,164.81,196,261.63],[49,98,130.81,164.81,196]];
    const now = state.audioContext.currentTime;
    for (const voice of state.musicVoices) {
      voice.gain.gain.cancelScheduledValues(now);
      voice.gain.gain.setTargetAtTime(0.0001,now,0.35);
      voice.oscillator.stop(now+1.7);
    }
    state.musicVoices = chords[index].map((frequency,noteIndex) => {
      const oscillator = state.audioContext.createOscillator(), gain = state.audioContext.createGain();
      oscillator.type = 'sine'; oscillator.frequency.value = frequency;
      gain.gain.setValueAtTime(0.0001,now);
      gain.gain.exponentialRampToValueAtTime(noteIndex===0?0.045:0.019,now+1.2);
      oscillator.connect(gain); gain.connect(state.musicGain); oscillator.start(now); oscillator.onended = () => { oscillator.disconnect(); gain.disconnect(); };
      return {oscillator,gain};
    });
    state.chordIndex=(index+1)%chords.length;
    window.clearTimeout(state.chordTimer);
    state.chordTimer=window.setTimeout(()=>playChord(state.chordIndex),4200);
  }
  function drawHeart(x,y,size,color,alpha) {
    context.save(); context.translate(x,y); context.scale(size/16,size/16); context.globalAlpha=alpha; context.fillStyle=color; context.beginPath();
    context.moveTo(0,12); context.bezierCurveTo(-20,0,-10,-12,0,-5); context.bezierCurveTo(10,-12,20,0,0,12); context.fill(); context.restore();
  }
  function drawParticle(p,dt) {
    p.life+=dt; p.x+=p.vx*dt+Math.sin(p.life*2.5+p.rotation)*10*dt; p.y+=p.vy*dt;
    if(p.burst){p.vy+=45*dt;p.vx*=.995;} else if(p.kind==='petal'){p.vy+=5*dt;p.vx+=Math.sin(p.life*2+p.rotation)*3*dt;} else p.vy-=2*dt;
    p.rotation+=p.spin*dt; const alpha=Math.max(0,1-p.life/p.maxLife);
    if(p.kind==='heart') drawHeart(p.x,p.y,p.size,p.color,alpha);
    else { context.save(); context.translate(p.x,p.y); context.rotate(p.rotation); context.globalAlpha=alpha; context.fillStyle=p.kind==='confetti'?p.color:'#f591ae'; context.beginPath(); if(p.kind==='confetti') context.rect(-p.size/2,-p.size,p.size,p.size*1.8); else context.ellipse(0,0,p.size,p.size*.55,0,0,Math.PI*2); context.fill(); context.restore(); }
    return p.life<p.maxLife && p.y<state.height+25;
  }
  function frame(now) {
    const dt=Math.min((now-(state.lastFrame||now))/1000,.045); state.lastFrame=now; context.clearRect(0,0,state.width,state.height);
    for(const star of state.stars){context.globalAlpha=.24+(Math.sin(now/1000*star.speed+star.phase)+1)*.3;context.fillStyle='#fff4e5';context.beginPath();context.arc(star.x,star.y,star.radius,0,Math.PI*2);context.fill();} context.globalAlpha=1;
    if(state.running&&now-state.lastAmbient>340){state.lastAmbient=now;addParticle(Math.random()*state.width,state.height+8,Math.random()>.35?'petal':'heart');}
    state.particles=state.particles.filter(p=>drawParticle(p,dt));
    state.fireworks=state.fireworks.filter(f=>{f.life+=dt;const t=f.life/f.duration,r=t*Math.min(state.width,state.height)*.12;context.globalAlpha=Math.max(0,1-t);context.strokeStyle=f.color;context.lineWidth=1.5;context.shadowBlur=14;context.shadowColor=f.color;for(let i=0;i<18;i+=1){const a=Math.PI*2*i/18;context.beginPath();context.moveTo(f.x+Math.cos(a)*r*.75,f.y+Math.sin(a)*r*.75);context.lineTo(f.x+Math.cos(a)*r,f.y+Math.sin(a)*r);context.stroke();}context.shadowBlur=0;if(f.life>=f.duration)burst(f.x,f.y,22,'heart');return f.life<f.duration;});context.globalAlpha=1;
    if(state.running&&state.sceneIndex>=0){const scene=scenes[state.sceneIndex],elapsed=now-state.sceneStarted;progress.style.width=`${Math.min(100,((state.sceneIndex+Math.min(elapsed/scene.duration,1))/scenes.length)*100)}%`;if(elapsed>=scene.duration)enterScene(state.sceneIndex+1);}
    if(proposal.classList.contains('is-visible')&&Math.random()<.006)launchFirework(Math.random()*state.width,Math.random()*state.height*.46);
    requestAnimationFrame(frame);
  }
  async function startStory() {
    if(state.audioStarted)return; state.audioStarted=true; music.volume=.72;
    try{await music.play();audioNote.textContent='A little music for the moment';soundLabel.textContent='Music on';soundButton.classList.remove('is-muted');soundButton.setAttribute('aria-label','Mute music');}
    catch(error){music.pause();music.muted=true;try{const started=await startSynthMusic();if(started){state.audioStarted=true;audioNote.textContent='A soft moonlit score is playing';soundLabel.textContent='Music on';soundButton.classList.remove('is-muted');soundButton.setAttribute('aria-label','Mute music');}else{audioNote.textContent='Sound is unavailable. The story is still yours.';soundLabel.textContent='Music off';soundButton.classList.add('is-muted');}}catch{audioNote.textContent='Sound is unavailable. The story is still yours.';soundLabel.textContent='Music off';soundButton.classList.add('is-muted');}}
    state.running=true;startScreen.classList.add('is-hidden');startScreen.setAttribute('aria-hidden','true');enterScene(0);
  }
  function acceptProposal() {
    if(state.accepted)return;state.accepted=true;state.running=false;proposal.classList.remove('is-visible');proposal.setAttribute('aria-hidden','true');
    ending.classList.add('is-visible');ending.setAttribute('aria-hidden','false');sceneCount.textContent='Forever starts here';film.classList.add('is-focused','is-finale');
    for(let i=0;i<440;i+=1){const kind=Math.random()<.47?'heart':Math.random()<.84?'petal':'confetti';addParticle(Math.random()*state.width,Math.random()*state.height,kind,true);}
    for(let i=0;i<7;i+=1)launchFirework(state.width*(.1+Math.random()*.8),state.height*(.13+Math.random()*.37));
    status.textContent='You just made me the happiest person alive. I love you forever.';music.volume=.9;
  }
  $('#skipButton').addEventListener('click',()=>{if(state.running)enterScene(state.sceneIndex+1);});
  startButton.addEventListener('click',startStory); $('#yesButton').addEventListener('click',acceptProposal);
  soundButton.addEventListener('click',async()=>{if(state.audioContext){if(state.audioMuted){await state.audioContext.resume();state.audioMuted=false;state.musicGain.gain.setTargetAtTime(.72,state.audioContext.currentTime,.12);playChord(state.chordIndex);soundLabel.textContent='Music on';soundButton.classList.remove('is-muted');soundButton.setAttribute('aria-label','Mute music');}else{state.audioMuted=true;window.clearTimeout(state.chordTimer);state.musicGain.gain.setTargetAtTime(0,state.audioContext.currentTime,.12);soundLabel.textContent='Music off';soundButton.classList.add('is-muted');soundButton.setAttribute('aria-label','Enable music');}return;}if(music.paused){music.muted=false;try{await music.play();soundLabel.textContent='Music on';soundButton.classList.remove('is-muted');soundButton.setAttribute('aria-label','Mute music');}catch{try{const started=await startSynthMusic();if(started){soundLabel.textContent='Music on';soundButton.classList.remove('is-muted');soundButton.setAttribute('aria-label','Mute music');audioNote.textContent='A soft moonlit score is playing';}}catch{audioNote.textContent='Music is unavailable in this browser.';}}}else{music.pause();soundLabel.textContent='Music off';soundButton.classList.add('is-muted');soundButton.setAttribute('aria-label','Enable music');}});
  document.addEventListener('keydown',event=>{if(event.code==='Space'&&state.running){event.preventDefault();enterScene(state.sceneIndex+1);}else if((event.key.toLowerCase()==='y'||event.key==='Enter')&&proposal.classList.contains('is-visible'))acceptProposal();});
  window.addEventListener('resize',resizeCanvas,{passive:true}); makeCity(); resizeCanvas(); requestAnimationFrame(frame);
})();