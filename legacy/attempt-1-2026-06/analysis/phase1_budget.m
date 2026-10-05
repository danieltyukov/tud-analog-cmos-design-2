%% EE4525 Phase 1 — Specs & budget (freeze design-time numbers before sizing)
% Reproducible companion to analysis/01, 04, 08. Run: produces all Phase-1
% frozen numbers + two budget figures (report/figures/phase1_*.png) + a
% results file (analysis/phase1_results.txt) for later phases.
%
% Architecture & ratio are SETTLED (see analysis/01 §1, analysis/02):
%   single-stage gain-boosted cascode + current-reuse input + real SC-CMFB,
%   Cin:Cfb = 4:1  ->  residue gain Gcl = Cin/Cfb = 4, beta = Cfb/(Cin+Cfb) = 1/5.
% This script does NOT re-litigate those; it sizes the budget around them.

clear; clc;
outdir = fullfile('..','report','figures');   % run from analysis/
if ~exist(outdir,'dir'); outdir = fullfile('report','figures'); end  % or from repo root

%% ---------- 0. Physical + spec constants -------------------------------
q     = 1.602176634e-19;        % C
kB    = 1.380649e-23;           % J/K
T     = 300;                    % K
kT    = kB*T;                   % 4.142e-21 J
Vdd   = 1.8;                    % V, single rail (07 §5.1)
Vcm   = 0.9;                    % V, output common mode (mid-rail)

SNRdB   = 66;                   % spec row 1 / loop accuracy row 2
SNRlin  = 10^(SNRdB/20);        % 1995.26
Asettle = 78;                   % dB, amplifier settling row 3
Tsettle = 25e-9;               % s, row 4 (= Tclk/2, 20 MS/s, 50% duty)
Fclk    = 20e6;                % Hz
Areq    = 4;                   % residue gain = Cin/Cfb (settled)
beta    = 1/5;                 % feedback factor (settled)
invbeta = 1/beta;             % 5 = noise gain = 1 + Cin/Cfb

%% ---------- 1. Settling: N_settle, tau, GBW ----------------------------
Nsettle = log(SNRlin);                 % e-folds to 66 dB accuracy = ln(1995)
tau_max = Tsettle/Nsettle;             % closed-loop tau ceiling
fu_loop = 1/(2*pi*tau_max);            % loop unity-gain freq (Hz)
GBW_amp = fu_loop*invbeta;             % open-loop amplifier GBW = fu/beta

% design with a little margin (slewing + parasitics eat into the 25 ns)
tau_des = 3.0e-9;                       % design target (< tau_max)

%% ---------- 2. Output swing decision (the one Phase-1 free DOF) --------
% Telescopic + current-reuse on 1.8 V limits headroom; pick a moderate,
% defensible single-ended swing. Ryu 2007 (same process) is the existence proof.
Vse_amp   = 0.45;                       % single-ended amplitude per node (V)
Vse_pp    = 2*Vse_amp;                  % single-ended peak-peak = 0.9 V (0.45..1.35 V)
Vdiff_amp = 2*Vse_amp;                  % differential amplitude = 0.9 V
Vdiff_pp  = 2*Vdiff_amp;                % differential pp = 1.8 V
Vsig_rms  = Vdiff_amp/sqrt(2);          % rms of full-swing diff sinusoid
eta_vol   = Vse_pp/Vdd;                 % Bult voltage efficiency (single-ended pp / Vdd)

%% ---------- 3. Noise budget + 50/50 split -----------------------------
Vn_tot_max = Vsig_rms/SNRlin;           % total output-referred diff noise ceiling
Vn_kTC_tgt = Vn_tot_max/sqrt(2);        % 50% power split -> kT/C share
Vn_amp_tgt = Vn_tot_max/sqrt(2);        % 50% power split -> amplifier share

%% ---------- 4. Solve Cin from kT/C share, freeze caps ------------------
% Repo-adopted differential sampled-noise form (04): Vn_kTC^2 = 2*(1/beta)^2*kT/Cin
kTC_prefactor = 2*invbeta^2;            % = 50
Cin_min  = kTC_prefactor*kT / Vn_kTC_tgt^2;   % minimum Cin for the 50% split
Cin      = 5e-12;                       % FROZEN (round up from Cin_min for margin)
Cfb      = Cin/Areq;                     % 1.25 pF  (4:1)
Cload    = Cin;                          % = Cin (spec row 17)
Vn_kTC   = sqrt(kTC_prefactor*kT/Cin);   % achieved kT/C noise at frozen Cin

% cross-check vs Bult unified SC form (08 §7): kT/Cfb*(Gain+1), differential x2
Vn_kTC_bult = sqrt(2*(kT/Cfb)*(Areq+1));

%% ---------- 5. First-cut gm from settling, then bias current ----------
% Effective output-node load incl. feedback loading: CLeff = Cload + Cfb*(1-beta)
CLeff = Cload + Cfb*(1-beta);
gm_req = CLeff/(beta*tau_des);          % gm = CLeff/(beta*tau)   (loop single-pole)
gm_bult = Areq*Cload/tau_des;           % Bult simplified chain (cross-check)

% current via gm/ID (input pair in weak/moderate inversion)
gm_ID_lo = 15;  gm_ID_hi = 24;          % 1/V  (moderate .. deep WI)
% current-reuse: gm_tot = gmN + gmP = 2*(gm/ID)*Ibranch  (N,P share one branch I)
Ibranch_lo = gm_req/(2*gm_ID_hi);       % deep WI  -> least current
Ibranch_hi = gm_req/(2*gm_ID_lo);       % moderate -> most current
Iin_lo = 2*Ibranch_lo;  Iin_hi = 2*Ibranch_hi;   % 2 branches in the diff pair
% without current-reuse (for comparison): plain diff pair tail = 2*gm/(gm/ID)
% (reuse makes gmN+gmP per branch -> same gm at half the supply current)
Iin_noreuse_lo = 2*gm_req/gm_ID_hi;  Iin_noreuse_hi = 2*gm_req/gm_ID_lo;

%% ---------- 6. Power: top-down floor + first-cut F_circuit/FoM ---------
Psystem = 32*kT*Fclk*Areq^2*SNRlin^2;   % implementation-independent floor (Bult)
n_body  = 1.6;  UT = kT/q;
Fsupply = Vdd/(n_body*UT);              % supply lever ~43.5

% efficiency factors (Phase-1 first-cut; refine after sizing in 08)
eta_gm = 0.6;  NEF = 1.5;  eta_cur = 0.5;     % carried from 08 §5
Fcircuit = 0.5*(1/eta_gm)*Nsettle*NEF/(eta_cur*eta_vol^2);
P_topdown = Psystem*Fcircuit/Fsupply;          % predicted amplifier power
Idd_topdown = P_topdown/Vdd;

% bottom-up cross-check from the sized current (input stage + ~30% overhead)
Iin_mid = mean([Iin_lo Iin_hi]);
Idd_botup = Iin_mid*1.3;
P_botup   = Idd_botup*Vdd;

% FoM: graded form  +  clean identity (08 §6) -- both at the top-down P
FoMlin_floor = 2*pi*Psystem*tau_max/SNRlin^2;            % at the floor power
FoMdB_floor  = -10*log10(FoMlin_floor);
FoMlin_td = 2*pi*P_topdown*tau_max/SNRlin^2;             % at top-down power
FoMdB_td  = -10*log10(FoMlin_td);
FoMlin_id = 16*pi*kT*Areq^2*NEF/(eta_gm*eta_cur*eta_vol^2*Fsupply);  % identity
FoMdB_id  = -10*log10(FoMlin_id);
FoMlin_bu = 2*pi*P_botup*tau_des/SNRlin^2;               % at bottom-up power
FoMdB_bu  = -10*log10(FoMlin_bu);

%% ---------- 7. Report all frozen numbers ------------------------------
L = {};
p = @(varargin) assignin('base','L',[evalin('base','L'), {sprintf(varargin{:})}]);
p('======================================================================');
p(' EE4525 Phase 1 - Specs & budget (FROZEN design-time numbers)');
p('======================================================================');
p('-- Settling --------------------------------------------------------');
p('  SNRlin            = %.1f', SNRlin);
p('  N_settle=ln(SNR)  = %.3f e-folds', Nsettle);
p('  tau_cl ceiling    = %.3f ns   (=25ns/N_settle)', tau_max*1e9);
p('  tau_cl design tgt = %.3f ns   (margin for slew+parasitics)', tau_des*1e9);
p('  loop f_u          = %.1f MHz', fu_loop/1e6);
p('  amp GBW (=fu/beta)= %.1f MHz', GBW_amp/1e6);
p('-- Output swing (single Phase-1 DOF) -------------------------------');
p('  output CM         = %.2f V', Vcm);
p('  single-ended swing= +/-%.2f V  (%.2f..%.2f V), se pp = %.2f V', ...
    Vse_amp, Vcm-Vse_amp, Vcm+Vse_amp, Vse_pp);
p('  differential swing= +/-%.2f V  (diff pp = %.2f V)', Vdiff_amp, Vdiff_pp);
p('  Vsig_rms,diff     = %.3f V', Vsig_rms);
p('  eta_vol (se pp/Vdd)= %.3f   (08 first-cut used 0.7-optimistic)', eta_vol);
p('-- Noise budget ----------------------------------------------------');
p('  Vn_tot max        = %.1f uV   (=Vsig_rms/SNRlin)', Vn_tot_max*1e6);
p('  Vn_kTC target(50%%)= %.1f uV', Vn_kTC_tgt*1e6);
p('  Vn_amp target(50%%)= %.1f uV', Vn_amp_tgt*1e6);
p('-- Capacitors (FROZEN) ---------------------------------------------');
p('  Cin_min for split = %.2f pF', Cin_min*1e12);
p('  Cin               = %.2f pF  (frozen, margin over min)', Cin*1e12);
p('  Cfb               = %.3f pF  (Cin/4)', Cfb*1e12);
p('  Cload             = %.2f pF  (=Cin)', Cload*1e12);
p('  -> Vn_kTC achieved= %.1f uV  (< %.1f uV target, OK)', Vn_kTC*1e6, Vn_kTC_tgt*1e6);
p('  -> Bult x-check   = %.1f uV  (2*kT/Cfb*(Gain+1), same order)', Vn_kTC_bult*1e6);
p('-- First-cut gm + bias current -------------------------------------');
p('  CLeff (out node)  = %.2f pF', CLeff*1e12);
p('  gm_req (loop)     = %.2f mS   (=CLeff/(beta*tau))', gm_req*1e3);
p('  gm  (Bult x-check)= %.2f mS', gm_bult*1e3);
p('  Iin w/ reuse      = %.0f .. %.0f uA  (gm/ID %d..%d)', ...
    Iin_lo*1e6, Iin_hi*1e6, gm_ID_lo, gm_ID_hi);
p('  Iin w/o reuse     = %.0f .. %.0f uA  (reuse ~halves it)', ...
    Iin_noreuse_lo*1e6, Iin_noreuse_hi*1e6);
p('-- Power / FoM (first-cut) -----------------------------------------');
p('  P_system floor    = %.3f mW   (32 kT Fclk Areq^2 SNR^2)', Psystem*1e3);
p('  F_supply          = %.1f', Fsupply);
p('  F_circuit         = %.1f   (eta_gm=%.1f NEF=%.1f eta_cur=%.1f eta_vol^2=%.3f)', ...
    Fcircuit, eta_gm, NEF, eta_cur, eta_vol^2);
p('  P top-down        = %.3f mW  (Idd=%.0f uA)', P_topdown*1e3, Idd_topdown*1e6);
p('  P bottom-up x-chk = %.3f mW  (Idd=%.0f uA, input+30%%)', P_botup*1e3, Idd_botup*1e6);
p('  FoM_dB @ floor    = %.1f dB', FoMdB_floor);
p('  FoM_dB @ top-down = %.1f dB   (identity: %.1f dB)', FoMdB_td, FoMdB_id);
p('  FoM_dB @ bottom-up= %.1f dB', FoMdB_bu);
p('  pass needs > 170 dB and < 3 mW: %s', ...
    string((FoMdB_td>170)&&(P_topdown<3e-3)));
p('======================================================================');
txt = strjoin(L, newline);
disp(txt);
fid = fopen(fullfile('phase1_results.txt'),'w');
if fid<0; fid = fopen(fullfile('analysis','phase1_results.txt'),'w'); end
fprintf(fid,'%s\n',txt); fclose(fid);

%% ---------- 8. Figure 1: noise budget vs Cin -------------------------
Cin_sweep = linspace(2,20,400)*1e-12;
VnkTC_sweep = sqrt(kTC_prefactor*kT./Cin_sweep)*1e6;     % uV
f1 = figure('Color','w','Position',[100 100 720 460]);
plot(Cin_sweep*1e12, VnkTC_sweep,'b-','LineWidth',2); hold on;
yline(Vn_kTC_tgt*1e6,'--','color',[0.85 0.33 0.10],'LineWidth',1.5, ...
    'Label','50% budget (kT/C share)','LabelHorizontalAlignment','left');
yline(Vn_tot_max*1e6,':','color',[0.2 0.2 0.2],'LineWidth',1.5, ...
    'Label','total noise ceiling','LabelHorizontalAlignment','left');
plot(Cin*1e12, Vn_kTC*1e6,'ko','MarkerFaceColor',[0.20 0.65 0.30],'MarkerSize',10);
text(Cin*1e12+0.4, Vn_kTC*1e6, sprintf('  frozen C_{in}=%.0f pF\n  %.0f \\muV_{rms}', ...
    Cin*1e12, Vn_kTC*1e6),'FontSize',10);
grid on; xlabel('C_{in}  [pF]'); ylabel('kT/C output noise (diff)  [\muV_{rms}]');
title('Phase 1 noise budget: kT/C vs C_{in}  (SNR 66 dB, 50/50 split)');
legend({'2(1/\beta)^2 kT/C_{in}'},'Location','northeast');
saveas(f1, fullfile(outdir,'phase1_noise_budget.png'));

%% ---------- 9. Figure 2: FoM vs swing (eta_vol), design point --------
etav_sweep = linspace(0.30,0.80,300);
Fcirc_sweep = 0.5*(1/eta_gm)*Nsettle*NEF./(eta_cur*etav_sweep.^2);
P_sweep = Psystem.*Fcirc_sweep/Fsupply;
FoMlin_sweep = 2*pi*P_sweep*tau_max/SNRlin^2;
FoMdB_sweep = -10*log10(FoMlin_sweep);
f2 = figure('Color','w','Position',[100 100 760 460]);
yyaxis left
plot(etav_sweep, FoMdB_sweep,'-','LineWidth',2); hold on;
yline(170,'--','LineWidth',1.4,'Label','pass: FoM > 170 dB');
plot(eta_vol, FoMdB_td,'o','MarkerSize',10,'MarkerFaceColor','auto');
text(eta_vol+0.01, FoMdB_td, sprintf('  design: \\eta_{vol}=%.2f, %.0f dB', eta_vol, FoMdB_td));
ylabel('FoM_{dB}  [dB]');
yyaxis right
plot(etav_sweep, P_sweep*1e3,'-','LineWidth',2);
ylabel('predicted amplifier power  [mW]');
grid on; xlabel('\eta_{vol} = V_{sig,pp,se}/V_{dd}  (output swing)');
title('Phase 1 FoM & power vs output swing  (top-down Bult model)');
saveas(f2, fullfile(outdir,'phase1_fom_power.png'));

disp('Saved figures: phase1_noise_budget.png, phase1_fom_power.png');
disp('Saved results: phase1_results.txt');
