// ============================================================================
// GreatLife Member Portal — Supabase connection
//
// FILL THESE IN from your Supabase project (Project Settings > API):
//   SUPABASE_URL      -> "Project URL"
//   SUPABASE_ANON_KEY  -> "anon / public" key (safe to expose in front-end code —
//                          Row Level Security is what actually protects the data)
// ============================================================================

const SUPABASE_URL = "https://zeslbujpjagrfnqipvji.supabase.co";
const SUPABASE_ANON_KEY = "sb_publishable_keGkxgVA_UQ6MVrGUt3DYQ_IbfD1r-2";

const supabaseClient = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

// ----------------------------------------------------------------------------
// Session guard — redirects to login if not signed in.
// Call requireSession() at the top of every protected page.
// ----------------------------------------------------------------------------
async function requireSession() {
  const { data: { session } } = await supabaseClient.auth.getSession();
  if (!session) {
    window.location.href = "index.html";
    return null;
  }
  return session;
}

// ----------------------------------------------------------------------------
// Fetches (or lazily creates) the members row tied to the logged-in auth user.
// Every module page needs this member_id to read/write its own data.
// ----------------------------------------------------------------------------
async function getOrCreateMemberRecord(session) {
  const { data: existing, error: fetchErr } = await supabaseClient
    .from("members")
    .select("*")
    .eq("auth_user_id", session.user.id)
    .maybeSingle();

  if (fetchErr) {
    console.error("Error fetching member record:", fetchErr);
    return null;
  }

  if (existing) return existing;

  // First login after signup — create their member record.
  const { data: created, error: createErr } = await supabaseClient
    .from("members")
    .insert({
      auth_user_id: session.user.id,
      member_name: session.user.user_metadata?.full_name || session.user.email,
      start_date: new Date().toISOString().slice(0, 10),
    })
    .select()
    .single();

  if (createErr) {
    console.error("Error creating member record:", createErr);
    return null;
  }
  return created;
}

async function signOut() {
  await supabaseClient.auth.signOut();
  window.location.href = "index.html";
}
