# Sierra Chart → Lucid Trading through Rithmic — the click path

The written checklist from the video **How I Copy Trade 5 Lucid Accounts From Sierra Chart** (video 9 in the
[library](../README.md#the-library--one-component-per-video)). One Sierra Chart lead account, four followers copied
by Rithmic's Trade Copier in R | Trader Pro. Keep this beside you while you set it up; the reasoning is in the video.

**What it gets you:** Sierra Chart placing the order on one Lucid account and Rithmic copying it to the others, with
the chartbook in this repo (`sierra/chartbooks/OPTD.Cht`) as a starting point.
**What it does not get you:** identical fills across five accounts (the copier sends separate orders), a strategy,
or a reason to skip the evaluation. Test on an evaluation or simulated funded account first.

Sources, read them yourself — pages change:
Lucid's Rithmic setup page (https://lucidtrading.com/rithmic-setup/) · Sierra Chart's Rithmic page
(https://www.sierrachart.com/index.php?l=doc/Rithmic.php) · Lucid's prohibited-hedging rule
(https://support.lucidtrading.com/en/articles/11404734-prohibited-hedging) · Lucid's copier installation guide
(https://www.lucidtrading.com/rithmic-copier-trader-installation-guide/) · Sierra Chart's own multi-account option,
Order Allocation to Trade Accounts (https://www.sierrachart.com/index.php?page=doc/OrderAllocationToTradeAccounts.html).

---

## 0 · The rule before every order

**Every chart and every DOM that can trade must show the same lead account.** Sierra Chart saves the Trade
Account choice per view. Switching tabs loads whatever that view last saved, so one chart pointing at a follower
bypasses the leader and the copy structure, and one account can end up long while another is short. Lucid treats
opposing positions across accounts as prohibited hedging, even if it lasts seconds and started as a wrong tab.

- [ ] After you change a chartbook, check the selector on every trade-enabled chart and DOM.
- [ ] Before you place the trade, check it again.
- [ ] After the trade, every order shows on the Rithmic side.

## 1 · Get the Rithmic side ready

- [ ] Lucid gives you **one** Rithmic User ID and password (dashboard and email). It is not one account's label;
      the one login pulls in every Lucid account attached to it. Never paste it anywhere visible.
- [ ] Download **R | Trader Pro** from Lucid's setup page.
- [ ] First login, as Lucid currently specifies: System `LucidTrading`, Gateway `Chicago Area`.
- [ ] Enter the User ID and password exactly. Both are case-sensitive.
- [ ] Complete the required market-data exchange agreements.
- [ ] Lucid says you can close R | Trader Pro after the agreements if you only need another platform. Leave it
      open: the Trade Copier and the positions view live here.

## 2 · Connect Sierra Chart

- [ ] `Global Settings → Data/Trade Service Settings` → Current Service: **Rithmic Direct - DTC [Trading]**.
- [ ] Press OK, wait a few seconds, reopen the window. The server list only populates after the service is
      selected.
- [ ] Choose the Lucid server named in Lucid's current instructions.
- [ ] Trading Username = the Rithmic User ID. Trading Password = the Rithmic password. Case-sensitive.
- [ ] Connect to the data feed. The Lucid accounts attached to that login appear in Sierra Chart's Trade Account
      selector. That is the connection.

## 3 · Symbols and time zone (the part that actually confuses people)

- [ ] Contract names change when you move from Teton, Tradovate or another service to Rithmic. Use
      `File → Find Symbol` for the service you are connected to and translate the symbols in your existing chartbook.
      Do not assume the old contract name still works.
- [ ] Check the chart time zone against your trading session, especially in a borrowed chartbook.
- [ ] If you already have a chartbook, keep it and use this list to update the connection, symbols and lead account.
      Starting fresh: `sierra/chartbooks/OPTD.Cht` in this repo. The chartbook never contains credentials; those stay
      in Data/Trade Service Settings on your machine.

## 4 · One lead, four followers (R | Trader Pro, not Sierra Chart)

Sierra Chart has its own multi-account feature, Order Allocation to Trade Accounts. This path uses Rithmic's copier
instead, so the copy layer stays with the broker connection.

- [ ] Trade Copier → **Add Copy From** → select the lead account.
- [ ] **Add Copy To** → add each account that follows it.
- [ ] **Enable** each row, the lead and every follower. A follower that is listed but not enabled is not part of the
      copy.
- [ ] Back in Sierra Chart, select that same lead on every chart you trade from. You do not select all five in Sierra
      Chart. One order on the lead; Rithmic sends the copies.

## 5 · Prove it, then keep watching it

- [ ] On an evaluation or simulated funded account: place one small resting limit far from price from the Sierra
      Chart DOM. Watch the long / short exposure numbers in R | Trader Pro: every account shows the order.
- [ ] Cancel it from Sierra Chart. It clears on both sides.
- [ ] Pass condition: account, contract, side, quantity and price match in Rithmic and Sierra Chart, and the cancel
      clears both.
- [ ] The copier is not atomic. A limit can fill the leader first, fill followers at different prices, or not fill a
      follower at all; market orders spread the difference wider. Lucid's own copier guide warns about delays,
      omissions, duplications and latency. Balances drift from identical setups for this reason.
- [ ] Keep the Rithmic positions view open while you trade. If one account disagrees, stop, reconcile every
      account, then place the next order.

## 6 · Data and routing are separate jobs

Market data and order routing are two rails. In the video's setup Sierra Chart's Denali feed carries the market data
(depth, history, chartbooks, indicators) and Rithmic only routes the orders to Lucid. If your Lucid plan includes
Rithmic data you can use that in Sierra Chart instead. If you use Denali, confirm your Sierra Chart package and CME
entitlement separately: a prop evaluation or simulated funded account is not the live funded brokerage account the
CME's nonprofessional check asks for.

---

Method free, no signals, no live P&L. Questions about this path go in the video's comments.
