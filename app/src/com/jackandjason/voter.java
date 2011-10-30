package com.jackandjason;

import java.io.IOException;

import android.app.Activity;
import android.os.Bundle;
import android.view.View;
import android.view.View.OnClickListener;
import android.widget.Button;
import android.widget.TextView;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.view.KeyEvent;
import android.app.AlertDialog;
import android.content.DialogInterface;
import java.net.InetAddress;
import android.content.Intent;

public class voter extends Activity {
    /** Called when the activity is first created. */

	WebView webview;
	private String HOST = "141.212.236.105";
	private String HOST_ADDRESS = "http://" + HOST + ":8888/vote";
	private class VoteViewClient extends WebViewClient {
		public Activity context;
		@Override
		public boolean shouldOverrideUrlLoading(WebView view, String url) {
			view.loadUrl(url);
			return true;
		}

		@Override
			public void onReceivedError(WebView view, int errorCode, String description, String failingUrl)
			{
		  	this.showError();
			}
	private void showError()
	{
		AlertDialog.Builder builder = new AlertDialog.Builder(this.context);
		  	builder.setCancelable(true);
		  	//builder.setIcon(R.drawable.dialog_question);
		  	builder.setTitle("Host not Reachable: " + HOST_ADDRESS);
		  	builder.setInverseBackgroundForced(true);
		  	builder.setPositiveButton("Retry", new DialogInterface.OnClickListener() {
		  		@Override
		  		public void onClick(DialogInterface dialog, int which)
					{
						// Retru connection
						Intent intent = getIntent();
						finish();
						startActivity(intent);
						dialog.dismiss();
					}
				});
			builder.setNegativeButton("Close", new DialogInterface.OnClickListener() {
				@Override
				public void onClick(DialogInterface dialog, int which) {
					// Close the application
		  		dialog.dismiss();
		  		Intent intent = new Intent(Intent.ACTION_MAIN);
		  		intent.addCategory(Intent.CATEGORY_HOME);
		  		intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
		  		startActivity(intent);
				}
			});
			AlertDialog alert = builder.create();
			alert.show();
	}
	}

	@Override
		protected void onCreate(Bundle savedInstanceState) {
			super.onCreate(savedInstanceState);

					webview = new WebView(this);
					setContentView(webview);

					webview.loadUrl(HOST_ADDRESS);
					webview.getSettings().setJavaScriptEnabled(true);
					webview.setVerticalScrollBarEnabled(false);
					webview.setHorizontalScrollBarEnabled(false);
					VoteViewClient vvc = new VoteViewClient();
					vvc.context = this;
					webview.setWebViewClient(vvc);
		}

	@Override
		public boolean onKeyDown(int keyCode, KeyEvent event) {
			if ((keyCode == KeyEvent.KEYCODE_BACK) && webview.canGoBack()) {
				webview.goBack();
				return true;
			}
			return super.onKeyDown(keyCode, event);
		}	
}
