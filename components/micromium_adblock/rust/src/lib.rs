//! C ABI bridge between RustAdblockEngine (C++) and the adblock crate.
//!
//! The C++ side sees an opaque `void*` handle. All strings are (ptr, len)
//! byte slices; rules text is the same newline-separated filter lists the
//! fallback engine consumes, so both backends share inputs exactly.
//! Production hardening: switch the raw C ABI to a `cxx` bridge once the
//! crate is vendored into //third_party/rust (see ../RUST_BACKEND.md).

use adblock::Engine;
use adblock::lists::FilterSet;
use adblock::request::Request;
use std::slice;
use std::str;

/// Rebuilt on every LoadFilterList call; the C++ service loads lists rarely
/// (startup + updater tick), so full rebuild keeps semantics simple.
pub struct Handle {
    engine: Engine,
    rule_count: usize,
}

#[no_mangle]
pub extern "C" fn micromium_adblock_rust_create() -> *mut Handle {
    let boxed = Box::new(Handle {
        engine: Engine::default(),
        rule_count: 0,
    });
    Box::into_raw(boxed)
}

#[no_mangle]
pub extern "C" fn micromium_adblock_rust_destroy(handle: *mut Handle) {
    if !handle.is_null() {
        unsafe {
            drop(Box::from_raw(handle));
        }
    }
}

#[no_mangle]
pub extern "C" fn micromium_adblock_rust_add_rules(
    handle: *mut Handle,
    rules_data: *const u8,
    rules_len: usize,
) {
    if handle.is_null() {
        return;
    }
    let bytes = unsafe { slice::from_raw_parts(rules_data, rules_len) };
    let text = str::from_utf8(bytes).unwrap_or("");
    // FilterSet parses full EasyList syntax;DEBUG filters (element hiding)
    // are kept out of network matching by `check_network_urls` below.
    let mut filter_set = FilterSet::new(false);
    let mut count = 0usize;
    for line in text.lines() {
        let line = line.trim();
        if line.is_empty() || line.starts_with('!') || line.starts_with('[') {
            continue;
        }
        filter_set.add_filter(line, Default::default()).ok();
        count += 1;
    }
    let state = unsafe { &mut *handle };
    state.engine = Engine::from_filter_set(filter_set, true);
    state.rule_count = count;
}

#[no_mangle]
pub extern "C" fn micromium_adblock_rust_should_block(
    handle: *const Handle,
    url_data: *const u8,
    url_len: usize,
) -> i32 {
    if handle.is_null() {
        return 0;
    }
    let bytes = unsafe { slice::from_raw_parts(url_data, url_len) };
    let url = match str::from_utf8(bytes) {
        Ok(u) => u,
        Err(_) => return 0,
    };
    let state = unsafe { &*handle };
    // Minimal request context: full third-party/domain scoping is supplied
    // by the caller once the network-service hookup lands (RUST_BACKEND.md).
    let request = match Request::new(url, url, "other") {
        Ok(r) => r,
        Err(_) => return 0,
    };
    if state.engine.check_network_urls(&request).blocked {
        1
    } else {
        0
    }
}

#[no_mangle]
pub extern "C" fn micromium_adblock_rust_rule_count(handle: *const Handle) -> usize {
    if handle.is_null() {
        return 0;
    }
    unsafe { (*handle).rule_count }
}
