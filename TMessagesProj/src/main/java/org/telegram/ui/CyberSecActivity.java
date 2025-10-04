package org.telegram.ui;

import android.content.Context;
import android.view.View;
import android.view.ViewGroup;
import android.widget.FrameLayout;

import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;

import org.telegram.messenger.AndroidUtilities;
import org.telegram.messenger.LocaleController;
import org.telegram.messenger.R;
import org.telegram.messenger.SharedConfig;
import org.telegram.ui.ActionBar.ActionBar;
import org.telegram.ui.ActionBar.BaseFragment;
import org.telegram.ui.ActionBar.Theme;
import org.telegram.ui.Cells.HeaderCell;
import org.telegram.ui.Cells.ShadowSectionCell;
import org.telegram.ui.Cells.TextCheckCell;
import org.telegram.ui.Cells.TextInfoPrivacyCell;
import org.telegram.ui.Components.LayoutHelper;
import org.telegram.ui.Components.RecyclerListView;

public class CyberSecActivity extends BaseFragment {

    private RecyclerListView listView;
    private ListAdapter listAdapter;

    private int headerRow;
    private int anonymousModeRow;
    private int hideIpRow;
    private int encryptMessagesRow;
    private int antiTrackingRow;
    private int secureDnsRow;
    private int infoRow;
    private int rowCount;

    @Override
    public boolean onFragmentCreate() {
        super.onFragmentCreate();
        updateRows();
        return true;
    }

    @Override
    public View createView(Context context) {
        actionBar.setBackButtonImage(R.drawable.ic_ab_back);
        actionBar.setAllowOverlayTitle(true);
        actionBar.setTitle(LocaleController.getString(R.string.CyberSecTitle));
        actionBar.setActionBarMenuOnItemClick(new ActionBar.ActionBarMenuOnItemClick() {
            @Override
            public void onItemClick(int id) {
                if (id == -1) {
                    finishFragment();
                }
            }
        });

        fragmentView = new FrameLayout(context);
        FrameLayout frameLayout = (FrameLayout) fragmentView;
        frameLayout.setBackgroundColor(Theme.getColor(Theme.key_windowBackgroundGray));

        listView = new RecyclerListView(context);
        listView.setLayoutManager(new LinearLayoutManager(context, LinearLayoutManager.VERTICAL, false));
        listView.setVerticalScrollBarEnabled(false);
        listView.setAdapter(listAdapter = new ListAdapter(context));
        frameLayout.addView(listView, LayoutHelper.createFrame(LayoutHelper.MATCH_PARENT, LayoutHelper.MATCH_PARENT));

        listView.setOnItemClickListener((view, position, x, y) -> {
            if (position == anonymousModeRow) {
                SharedConfig.toggleCyberSecAnonymousMode();
                if (view instanceof TextCheckCell) {
                    ((TextCheckCell) view).setChecked(SharedConfig.cyberSecAnonymousMode);
                }
            } else if (position == hideIpRow) {
                SharedConfig.toggleCyberSecHideIP();
                if (view instanceof TextCheckCell) {
                    ((TextCheckCell) view).setChecked(SharedConfig.cyberSecHideIP);
                }
            } else if (position == encryptMessagesRow) {
                SharedConfig.toggleCyberSecEncrypt();
                if (view instanceof TextCheckCell) {
                    ((TextCheckCell) view).setChecked(SharedConfig.cyberSecEncrypt);
                }
            } else if (position == antiTrackingRow) {
                SharedConfig.toggleCyberSecAntiTracking();
                if (view instanceof TextCheckCell) {
                    ((TextCheckCell) view).setChecked(SharedConfig.cyberSecAntiTracking);
                }
            } else if (position == secureDnsRow) {
                SharedConfig.toggleCyberSecSecureDNS();
                if (view instanceof TextCheckCell) {
                    ((TextCheckCell) view).setChecked(SharedConfig.cyberSecSecureDNS);
                }
            }
        });

        return fragmentView;
    }

    private void updateRows() {
        rowCount = 0;
        headerRow = rowCount++;
        anonymousModeRow = rowCount++;
        hideIpRow = rowCount++;
        encryptMessagesRow = rowCount++;
        antiTrackingRow = rowCount++;
        secureDnsRow = rowCount++;
        infoRow = rowCount++;
    }

    private class ListAdapter extends RecyclerListView.SelectionAdapter {

        private Context mContext;

        public ListAdapter(Context context) {
            mContext = context;
        }

        @Override
        public int getItemCount() {
            return rowCount;
        }

        @Override
        public void onBindViewHolder(RecyclerView.ViewHolder holder, int position) {
            switch (holder.getItemViewType()) {
                case 0: {
                    HeaderCell headerCell = (HeaderCell) holder.itemView;
                    if (position == headerRow) {
                        headerCell.setText(LocaleController.getString(R.string.CyberSecTitle));
                    }
                    break;
                }
                case 1: {
                    TextCheckCell textCheckCell = (TextCheckCell) holder.itemView;
                    if (position == anonymousModeRow) {
                        textCheckCell.setTextAndCheck(LocaleController.getString(R.string.CyberSecAnonymousMode), SharedConfig.cyberSecAnonymousMode, true);
                    } else if (position == hideIpRow) {
                        textCheckCell.setTextAndCheck(LocaleController.getString(R.string.CyberSecHideIP), SharedConfig.cyberSecHideIP, true);
                    } else if (position == encryptMessagesRow) {
                        textCheckCell.setTextAndCheck(LocaleController.getString(R.string.CyberSecEncryptMessages), SharedConfig.cyberSecEncrypt, true);
                    } else if (position == antiTrackingRow) {
                        textCheckCell.setTextAndCheck(LocaleController.getString(R.string.CyberSecAntiTracking), SharedConfig.cyberSecAntiTracking, true);
                    } else if (position == secureDnsRow) {
                        textCheckCell.setTextAndCheck(LocaleController.getString(R.string.CyberSecSecureDNS), SharedConfig.cyberSecSecureDNS, false);
                    }
                    break;
                }
                case 2: {
                    TextInfoPrivacyCell textInfoPrivacyCell = (TextInfoPrivacyCell) holder.itemView;
                    if (position == infoRow) {
                        textInfoPrivacyCell.setText(LocaleController.getString(R.string.CyberSecInfo));
                        textInfoPrivacyCell.setBackgroundDrawable(Theme.getThemedDrawable(mContext, R.drawable.greydivider_bottom, Theme.key_windowBackgroundGrayShadow));
                    }
                    break;
                }
            }
        }

        @Override
        public boolean isEnabled(RecyclerView.ViewHolder holder) {
            int position = holder.getAdapterPosition();
            return position == anonymousModeRow || position == hideIpRow || 
                   position == encryptMessagesRow || position == antiTrackingRow || 
                   position == secureDnsRow;
        }

        @Override
        public RecyclerView.ViewHolder onCreateViewHolder(ViewGroup parent, int viewType) {
            View view;
            switch (viewType) {
                case 0:
                    view = new HeaderCell(mContext);
                    view.setBackgroundColor(Theme.getColor(Theme.key_windowBackgroundWhite));
                    break;
                case 1:
                    view = new TextCheckCell(mContext);
                    view.setBackgroundColor(Theme.getColor(Theme.key_windowBackgroundWhite));
                    break;
                case 2:
                default:
                    view = new TextInfoPrivacyCell(mContext);
                    break;
            }
            view.setLayoutParams(new RecyclerView.LayoutParams(RecyclerView.LayoutParams.MATCH_PARENT, RecyclerView.LayoutParams.WRAP_CONTENT));
            return new RecyclerListView.Holder(view);
        }

        @Override
        public int getItemViewType(int position) {
            if (position == headerRow) {
                return 0;
            } else if (position == infoRow) {
                return 2;
            } else {
                return 1;
            }
        }
    }
}
