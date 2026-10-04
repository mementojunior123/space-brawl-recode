const CHANNEL_COUNT = "`{CHANNEL_COUNT}`";
const channels = [];
const PATH_LIST = `{PATH_LIST}`;
const AUDIO_DICT = {};
for (let i = 0; i < PATH_LIST.length; i++) {
    let path = PATH_LIST[i];
    try {
        AUDIO_DICT[path] = new Audio(path);
    }
    catch(err) {
        console.log(`Tried to preload ${path}, but it does not exist`)
    }
}

class AudioChannel {
    constructor(path, id, volume, target_loop_count, active = false) {
        this.path = path;
        this.id = id;
        this.volume = volume;
        this.target_loop_count = target_loop_count;
        this.current_loop_count = 0;
        this.active = active;
        if (Object.hasOwn(AUDIO_DICT, path)) {
            this.audio = AUDIO_DICT[path]//.cloneNode(false);
        } else {
            this.audio = new Audio(path);
        }
        this.audio.onended = this.when_audio_ends;
        this.audio.volume = volume;
        if (!this.path.includes('audio/NOTHING.ogg')) {
            if (this.active) {
                this.audio.play().catch((r) => {});
                console.log(`Started audio playback of ${path} on channel ${id}`);
            } else {
                console.log(`Loaded audio ${path} on channel ${id}`);
            }
        } else {
            this.active = false;
            console.log(`Created web audio channel ${id}`)
        }
        const b = 'WebAudioChannel' + id.toString() + "_";
        localStorage.setItem(b + "volume", this.audio.volume.toString());
        localStorage.setItem(b + "busy", (active).toString());

        window.addEventListener('StartAudio', (ev) => {this.start_audio_ev(ev)});
        window.addEventListener('PauseAudio', (ev) => {this.pause_audio_ev(ev)});
        window.addEventListener('ResumeAudio', (ev) => {this.resume_audio_ev(ev)});
        window.addEventListener('StopAudio', (ev) => {this.stop_audio_ev(ev)});
        window.addEventListener('UpdateVolume', (ev) => {this.update_volume_ev(ev)});
        window.addEventListener('UpdateAudioChannel', (ev) => {this.update_channel_ev(ev)});

    }

    when_audio_ends(event) {
        if (event.target !== this.audio) {return;}
        if (this.target_loop_count < 0 || this.current_loop_count < this.target_loop_count) {
            this.current_loop_count += 1;
            this.audio.currentTime = 0;
            this.audio.play().catch((r) => {})
        } else {
            this.active = false;
            const base_key = 'WebAudioChannel' + id.toString() + "_";
            localStorage.setItem(base_key + "busy", (this.active).toString());
            console.log(`Ended audio playback of ${this.path} on channel ${this.id}`);
        }
    }

    start_audio_ev(event) {
        if (event.detail.id !== this.id) {return;}
        this.audio.pause();
        
        if (Object.hasOwn(AUDIO_DICT, event.detail.path)) {
            this.audio = AUDIO_DICT[event.detail.path].cloneNode(false);
        } else {
            this.audio = new Audio(event.detail.path);
        }
        this.audio.onended = this.when_audio_ends;
        this.audio.volume = event.detail.volume;
        this.volume = event.detail.volume;
        this.current_loop_count = 0;
        this.target_loop_count = event.detail.target_loop_count;
        
        if ((!event.detail.dont_play) || (event.detail.dont_play === undefined)) {
            this.audio.play().catch((r) => {});
            console.log(`Started audio playback of ${event.detail.path} on channel ${event.detail.id}`)
        } else {
            console.log(`Loaded audio ${event.detail.path} on channel ${event.detail.id}`)
        }
        this.path = event.detail.path;
        this.active = true;
    }

    stop_audio_ev(event) {
        if (event.detail.id !== this.id) {return;}
        this.audio.pause();
        console.log(`Stopped audio playback of ${this.path} on channel ${event.detail.id}`);
        const base_key = 'WebAudioChannel' + this.id.toString() + "_";
        localStorage.setItem(base_key + "volume", "0");
        localStorage.setItem(base_key + "busy", "false");
        this.active = false;
    }

    update_volume_ev(event) {
        if (event.detail.id !== this.id) {return;}
        this.audio.volume = event.detail.volume;
        this.volume = event.detail.volume
    }

    pause_audio_ev(event) {
        if (event.detail.id !== this.id) {return;}
        this.audio.pause();
    }

    resume_audio_ev(event) {
        if (event.detail.id !== this.id || !(this.active)) {return;}
        if (this.audio.paused) {
            this.audio.play().catch((r) => {});
        }
    }

    update_channel_ev(event) {
        if (event.detail.id !== this.id) {return;}
        const base_key = 'WebAudioChannel' + this.id.toString() + "_";
        localStorage.setItem(base_key + "volume", this.audio.volume.toString());
        localStorage.setItem(base_key + "busy", (this.active).toString());
    }
}
for (let i = 0; i < CHANNEL_COUNT; i++) {
    let channel = new AudioChannel("assets/audio/NOTHING.ogg", i, 1.0, 0, false);
    channels.push(channel);
}